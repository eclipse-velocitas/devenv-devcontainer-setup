# Copyright (c) 2024-2025 Contributors to the Eclipse Foundation
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

from shell_source import source
from velocitas_lib import get_valid_arch, get_workspace_dir

CMAKE_EXECUTABLE = "cmake"
CONAN_EXECUTABLE = "conan"


def safe_get_workspace_dir() -> str:
    """A safe version of get_workspace_dir which defaults to '.'."""
    try:
        return get_workspace_dir()
    except Exception:
        return os.path.abspath(".")


def get_build_folder(op_sys: str, arch: str, build_type: str) -> str:
    return os.path.join(f"build-{op_sys}-{arch}", build_type)


def safe_create_symlink_to_folder(target_folder: str, link_name: str):
    try:
        if os.readlink(link_name):
            os.remove(link_name)
    except FileNotFoundError:
        pass
    except OSError:
        print(f"File '{link_name}' exists, but is not a symlink. Will not overwrite!")
        return
    os.symlink(target_folder, link_name, target_is_directory=True)


def print_build_info(
    build_type: str,
    build_arch: str,
    host_arch: str,
    build_target: str,
    is_static_build: bool,
    coverage: bool,
) -> None:
    """Print information about the build.

    Args:
        build_type (str): The type of the build: "release" or "debug"
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
    print(f"Build type         {build_type}")
    print(f"Build target       {build_target}")
    print(f"Static build       {'yes' if is_static_build else 'no'}")
    print(f"Coverage enabled   {'yes' if coverage else 'no'}")


def build(
    build_type: str,
    build_arch: str,
    host_arch: str,
    build_target: str,
    static_build: bool,
    coverage: bool = False,
    num_jobs: int = 2,
) -> None:
    cxx_flags = ["-g"]
    if coverage:
        cxx_flags.append("--coverage")

    if build_type == "Release":
        cxx_flags.append("-s")
        cxx_flags.append("-O3")
    else:
        cxx_flags.append("-O0")

    build_folder = get_build_folder("linux", host_arch, build_type)
    os.makedirs(os.path.join(safe_get_workspace_dir(), build_folder), exist_ok=True)
    if build_arch == host_arch:
        safe_create_symlink_to_folder(
            build_folder, os.path.join(safe_get_workspace_dir(), "build")
        )

    build_env = source(
        os.path.join(build_folder, "generators/conanbuild.sh"),
        "bash",
        ignore_locals=True,
    )

    subprocess.run(
        [
            CMAKE_EXECUTABLE,
            "--no-warn-unused-cli",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=TRUE",
            f"-DCMAKE_BUILD_TYPE:STRING={build_type}",
            f"-DSTATIC_BUILD:BOOL={'ON' if static_build else 'OFF'}",
            f"-DCMAKE_CXX_FLAGS={' '.join(cxx_flags)}",
            "-DCMAKE_TOOLCHAIN_FILE=generators/conan_toolchain.cmake",
            "-G",
            "Ninja",
            "-S",
            safe_get_workspace_dir(),
            "-B.",
        ],
        cwd=build_folder,
        env=build_env,
    )
    subprocess.run(
        [
            CMAKE_EXECUTABLE,
            "--build",
            ".",
            "--target",
            build_target,
        ],
        cwd=build_folder,
        env=build_env,
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
        const="Debug",
        dest="build_type",
        help="Builds the target(s) in debug mode.",
    )
    parser.add_argument(
        "-r",
        "--release",
        action="store_const",
        const="Release",
        dest="build_type",
        help="Builds the target(s) in release mode.",
    )
    parser.add_argument(
        "-t", "--target", help="Builds only the target <name> instead of all targets."
    )
    parser.add_argument(
        "-j", "--jobs", help="Number of parallel jobs to use for building."
    )
    parser.add_argument(
        "-s", "--static", action="store_true", help="Links all dependencies statically."
    )
    parser.add_argument(
        "-x",
        "--cross",
        action="store",
        help="Enables cross-compilation to the defined target architecture.",
    )
    parser.add_argument("--coverage", action="store_true", help="Enable gtest coverage")

    args = parser.parse_args()
    if not args.build_type:
        args.build_type = "Debug"
    if not args.target:
        args.target = "all"
    build_arch = subprocess.check_output(["arch"], encoding="utf-8").strip()

    host_arch = args.cross
    if host_arch is None:
        host_arch = build_arch
    else:
        host_arch = get_valid_arch(host_arch)

    print_build_info(
        args.build_type, build_arch, host_arch, args.target, args.static, args.coverage
    )
    build(
        args.build_type,
        build_arch,
        host_arch,
        args.target,
        args.static,
        args.coverage,
        args.jobs,
    )


if __name__ == "__main__":
    cli()
