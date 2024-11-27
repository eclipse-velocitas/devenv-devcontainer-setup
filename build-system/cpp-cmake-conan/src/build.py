# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

import os
import subprocess
from argparse import ArgumentParser
from pathlib import Path

from utils import (
    get_build_folder,
    get_build_tools_path,
    load_toolchain,
    safe_get_workspace_dir,
)
from velocitas_lib import get_valid_arch

CMAKE_EXECUTABLE = "cmake"
CONAN_EXECUTABLE = "conan"


def print_build_info(
    build_variant: str,
    build_arch: str,
    host_arch: str,
    build_target: str,
    is_static_build: bool,
) -> None:
    """Print information about the build.

    Args:
        build_variant (str): The variant of the build: "release" or "debug"
        build_arch (str): The architecture the app is built for.
        build_target (str): Which artefact is being built.
        is_static_build (bool): Enable static building.
    """
    cmake_version = subprocess.check_output(
        [CMAKE_EXECUTABLE, "--version"], encoding="utf-8"
    ).strip()
    conan_version = subprocess.check_output(
        [CONAN_EXECUTABLE, "--version"], encoding="utf-8"
    ).strip()

    print(f"CMake version      {cmake_version}")
    print(f"Conan version      {conan_version}")
    print(f"Build arch         {build_arch}")
    print(f"Host arch          {host_arch}")
    print(f"Build variant      {build_variant}")
    print(f"Build target       {build_target}")
    print(f"Static build       {'yes' if is_static_build else 'no'}")


def build(
    build_variant: str,
    build_arch: str,
    host_arch: str,
    build_target: str,
    static_build: bool,
    toolchain_file: str = "",
    coverage: bool = True,
) -> None:
    xcompile_toolchain_file = ""
    if toolchain_file != "":
        load_toolchain(toolchain_file)
        xcompile_toolchain_file = f"-DCMAKE_TOOLCHAIN_FILE={os.environ.get('CMAKE_TOOLCHAIN_FILE', '').strip()}"
        cmake_cxx_flags = f"-DCMAKE_CXX_FLAGS={os.environ.get('CXXFLAGS', '')}"
        host_arch = os.environ.get("OECORE_TARGET_ARCH", build_arch).strip()

    else:
        cxx_flags = ["-g"]
        if coverage:
            cxx_flags.append("--coverage")

        if build_variant == "release":
            cxx_flags.append("-s")
            cxx_flags.append("-O3")
        else:
            cxx_flags.append("-O0")

        cmake_cxx_flags = f"-DCMAKE_CXX_FLAGS={' '.join(cxx_flags)}"

    build_folder = get_build_folder(build_arch, host_arch)
    os.makedirs(build_folder, exist_ok=True)

    if build_arch != host_arch and xcompile_toolchain_file == "":
        profile_build_path = (
            Path(__file__)
            .absolute()
            .parent.joinpath("cmake", f"{build_arch}_to_{host_arch}.cmake")
        )
        xcompile_toolchain_file = f"-DCMAKE_TOOLCHAIN_FILE={profile_build_path}"

    subprocess.run(
        [
            CMAKE_EXECUTABLE,
            "--no-warn-unused-cli",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=TRUE",
            f"-DCMAKE_BUILD_TYPE:STRING={build_variant}",
            f'-DBUILD_TOOLS_PATH:STRING="{get_build_tools_path(build_folder)}"',
            f"-DSTATIC_BUILD:BOOL={'TRUE' if static_build else 'FALSE'}",
            xcompile_toolchain_file,
            "-S",
            safe_get_workspace_dir(),
            "-B.",
            "-G",
            "Ninja",
            cmake_cxx_flags,
        ],
        cwd=build_folder,
    )
    subprocess.run(
        [
            CMAKE_EXECUTABLE,
            "--build",
            ".",
            "--config",
            build_variant,
            "--target",
            build_target,
        ],
        cwd=build_folder,
    )


def cli() -> None:
    parser = ArgumentParser(
        description="""Build targets of the project
============================================================================
Builds the targets of the project in different flavors."""
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const="debug",
        dest="variant",
        help="Builds the target(s) in debug mode.",
    )
    parser.add_argument(
        "-r",
        "--release",
        action="store_const",
        const="release",
        dest="variant",
        help="Builds the target(s) in release mode.",
    )
    parser.add_argument(
        "-t", "--target", help="Builds only the target <name> instead of all targets."
    )
    parser.add_argument(
        "-s", "--static", action="store_true", help="Links all dependencies statically."
    )
    parser.add_argument(
        "--toolchain",
        default="",
        help="Specify a file (absolute path) containing the definitions of a custom toolchain.",
    )
    parser.add_argument(
        "-x",
        "--cross",
        action="store",
        help="Enables cross-compilation to the defined target architecture.",
    )
    args = parser.parse_args()
    if not args.variant:
        args.variant = "debug"
    if not args.target:
        args.target = "all"
    build_arch = subprocess.check_output(["arch"], encoding="utf-8").strip()

    host_arch = args.cross

    if host_arch is None:
        host_arch = build_arch
    else:
        host_arch = get_valid_arch(host_arch)

    print_build_info(args.variant, build_arch, host_arch, args.target, args.static)
    build(args.variant, build_arch, host_arch, args.target, args.static, args.toolchain)


if __name__ == "__main__":
    cli()
