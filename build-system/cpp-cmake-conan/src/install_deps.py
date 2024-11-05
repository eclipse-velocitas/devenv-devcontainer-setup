# Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""
Install all software depenencies of the given Velocitas project via a
simple command line interface.
"""

import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path

from utils import get_build_folder, load_toolchain, safe_get_workspace_dir
from velocitas_lib import get_valid_arch


def get_profile_name(arch: str, build_variant: str) -> str:
    """Return the Conan profile name for the given `arch` and
    `build_variant`.

    Args:
        arch (str): The architecture of the profile.
        build_variant (str): The build variant (debug or release).

    Returns:
        str: The Conan profile name.
    """
    return f"linux_{get_valid_arch(arch)}_{build_variant}"


def get_valid_conan_arch(arch: str) -> str:
    """Return the valid architecture for the given `arch`.

    Args:
        arch (str): The architecture to validate.

    Returns:
        str: The valid architecture.
    """
    if arch == "x86_64":
        return "x86_64"
    elif arch == "aarch64" or arch == "armv8" or arch == "arm64":
        return "armv8"
    elif arch == "armv7":
        return "armv7"
    else:
        raise ValueError(f"Unsupported architecture: {arch}")


def install_deps_via_conan(
    build_arch: str,
    host_arch: str,
    is_debug: bool = False,
    build_all_deps: bool = False,
    toolchain_file: str = "",
) -> None:
    build_variant = "debug" if is_debug else "release"

    profile_build_path = (
        Path(__file__)
        .absolute()
        .parent.joinpath(
            ".conan", "profiles", get_profile_name(build_arch, build_variant)
        )
    )
    if toolchain_file != "":
        load_toolchain(toolchain_file)
        host_arch = get_valid_arch(
            os.environ.get("OECORE_TARGET_ARCH", build_arch).strip()
        )
        host_config = [
            "-s:h",
            f"arch={get_valid_conan_arch(host_arch)}",
            "-s:h",
            f"arch_build={get_valid_conan_arch(build_arch)}",
        ]
    else:
        profile_host_path = (
            Path(__file__)
            .absolute()
            .parent.joinpath(
                ".conan", "profiles", get_profile_name(host_arch, build_variant)
            )
        )
        host_config = ["-pr:h", f"{profile_host_path}"]

    build_folder = get_build_folder(build_arch, host_arch)
    os.makedirs(build_folder, exist_ok=True)

    deps_to_build = "missing" if not build_all_deps else "*"

    if toolchain_file == "":
        toolchain = f"/usr/bin/{host_arch}-linux-gnu"
        build_host = f"{host_arch}-linux-gnu"
        cc_compiler = "gcc"
        cxx_compiler = "g++"

        os.environ["CONAN_CMAKE_FIND_ROOT_PATH"] = toolchain
        os.environ["CONAN_CMAKE_SYSROOT"] = toolchain
        os.environ["CC"] = f"{build_host}-{cc_compiler}"
        os.environ["CXX"] = f"{build_host}-{cxx_compiler}"

    args = [
        "conan",
        "install",
        *host_config,
        "-pr:b",
        str(profile_build_path),
        "--build",
        deps_to_build,
        safe_get_workspace_dir(),
    ]
    subprocess.check_call(
        args,
        env=os.environ,
        cwd=build_folder,
    )


def cli() -> None:
    argument_parser = ArgumentParser(description="Installs dependencies")
    argument_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Installs all dependencies in debug mode.",
    )
    argument_parser.add_argument(
        "-r",
        "--release",
        action="store_true",
        help="Installs all dependencies in release mode.",
    )
    argument_parser.add_argument(
        "-ba",
        "--build-all-deps",
        action="store_true",
        help="Forces all dependencies to be rebuild from source.",
    )
    argument_parser.add_argument(
        "--toolchain",
        default="",
        help="Specify a file (absolute path) containing the definitions of a custom toolchain.",
    )
    argument_parser.add_argument(
        "-x",
        "--cross",
        action="store",
        help="Enables cross-compilation to the defined target architecture.",
    )
    args = argument_parser.parse_args()

    build_arch = subprocess.check_output(["arch"], encoding="utf-8").strip()

    host_arch = args.cross

    if host_arch is None:
        host_arch = build_arch
    else:
        host_arch = get_valid_arch(host_arch)

    subprocess.check_call(["conan", "config", "set", "general.revisions_enabled=1"])

    install_deps_via_conan(
        build_arch,
        host_arch,
        args.debug and not args.release,
        args.build_all_deps,
        args.toolchain,
    )


if __name__ == "__main__":
    cli()
