# Copyright (c) 2023-2025 Contributors to the Eclipse Foundation
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

from velocitas_lib import get_valid_arch, get_workspace_dir


def safe_get_workspace_dir() -> str:
    """A safe version of get_workspace_dir which defaults to '.'."""
    try:
        return get_workspace_dir()
    except Exception:
        return os.path.abspath(".")


def get_build_folder(op_sys: str, arch: str, build_type: str) -> str:
    return os.path.join(
        safe_get_workspace_dir(), f"build-{op_sys}-{arch}", f"{build_type}"
    )


def install_deps_via_conan(
    build_arch: str,
    host_arch: str,
    build_type: str,
    build_all_deps: bool = False,
) -> None:
    is_mixed_build = build_type == "Mixed"
    if is_mixed_build:
        build_type = "Release"
        print(
            f'--> "MIXED" build type detected - preparing build for pure {build_type} and "mixed" buid type:'
        )

    op_sys = "linux"

    profile_build_path = (
        Path(__file__)
        .absolute()
        .parent.joinpath(".conan", "profiles", f"{op_sys}-{build_arch}")
    )

    profile_host_path = (
        Path(__file__)
        .absolute()
        .parent.joinpath(".conan", "profiles", f"{op_sys}-{host_arch}")
    )

    deps_to_build = "missing" if not build_all_deps else "*"

    if is_mixed_build:
        print(
            '\n--> Installing dependencies for "mixed" build: Dependencies in Release mode, local stuff in Debug mode ...'
        )
        subprocess.check_call(
            [
                "conan",
                "install",
                "-pr:h",
                profile_host_path,
                "-pr:b",
                profile_build_path,
                "-s:a=build_type=Release",
                "-s:h=&:build_type=Debug",
                "--build",
                deps_to_build,
                "-of",
                os.path.join(
                    get_build_folder(op_sys, host_arch, "Debug"), "generators"
                ),
                safe_get_workspace_dir(),
            ],
            cwd=safe_get_workspace_dir(),
        )

    print(f"\n--> Installing dependencies for uniform build in {build_type} mode ...")
    subprocess.check_call(
        [
            "conan",
            "install",
            "-pr:h",
            profile_host_path,
            "-pr:b",
            profile_build_path,
            f"-s:a=build_type={build_type}",
            "--build",
            deps_to_build,
            "-of",
            os.path.join(get_build_folder(op_sys, host_arch, build_type), "generators"),
            safe_get_workspace_dir(),
        ],
        cwd=safe_get_workspace_dir(),
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

    build_type = "Mixed"
    if args.debug and not args.release:
        build_type = "Debug"
    elif args.release and not args.debug:
        build_type = "Release"

    install_deps_via_conan(build_arch, host_arch, build_type, args.build_all_deps)


if __name__ == "__main__":
    cli()
