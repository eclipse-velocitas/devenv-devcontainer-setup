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

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import conan_helper
from generator import GrpcInterfaceGenerator
from proto import ProtoFileHandle
from velocitas_lib import get_package_path

CONAN_PROFILE_NAME = "host"


class CppGrpcInterfaceGenerator(GrpcInterfaceGenerator):  # type: ignore
    def __init__(self, verbose: bool):
        self._verbose = verbose

    def __create_conan_profile(self) -> None:
        subprocess.check_call(
            ["conan", "profile", "new", CONAN_PROFILE_NAME, "--detect", "--force"],
            stdout=subprocess.DEVNULL,
        )

        subprocess.check_call(
            [
                "conan",
                "profile",
                "update",
                "settings.compiler.libcxx=libstdc++11",
                CONAN_PROFILE_NAME,
            ],
            stdout=subprocess.DEVNULL if not self._verbose else None,
        )

        subprocess.check_call(
            [
                "conan",
                "profile",
                "update",
                "settings.build_type=Release",
                CONAN_PROFILE_NAME,
            ],
            stdout=subprocess.DEVNULL if not self._verbose else None,
        )

    def __install_protoc_via_conan(self, conan_build_dir: str) -> None:
        env = os.environ.copy()
        env["CONAN_REVISIONS_ENABLED"] = "1"

        template_dir = os.path.join(
            get_package_path(), "grpc-interface-support", "templates", "cpp"
        )

        deps_to_extract = [
            "grpc",
            "c-ares",
            "googleapis",
            "grpc-proto",
            "zlib",
            "protobuf",
        ]
        deps_patterns = [
            re.compile(r"^.*\"(" + dep + r"\/.*)\".*$") for dep in deps_to_extract
        ]
        deps_results = []
        with open(
            os.path.join(template_dir, "conanfile.py"), encoding="utf-8"
        ) as conanfile:
            for line in conanfile:
                for pattern in deps_patterns:
                    match = pattern.match(line)
                    if match is not None:
                        deps_results.append(match.group(1))

        tmpdir = tempfile.mkdtemp()
        tooling_conanfile_path = os.path.join(tmpdir, "conanfile.txt")
        with open(
            tooling_conanfile_path, mode="w", encoding="utf-8"
        ) as tooling_conanfile:
            tooling_conanfile.write("[requires]\n" + "\n".join(deps_results))

        subprocess.check_call(
            [
                "conan",
                "install",
                "-pr:h",
                CONAN_PROFILE_NAME,
                "--build",
                "missing",
                tooling_conanfile_path,
            ],
            cwd=conan_build_dir,
            env=env,
            stdout=subprocess.DEVNULL if not self._verbose else None,
        )

    def __extend_path_with_protoc_and_plugin(self, conan_install_dir: str) -> None:
        with open(os.path.join(conan_install_dir, "conanbuildinfo.txt")) as buildinfo:
            for line in buildinfo:
                if line.startswith("PATH=["):
                    addition = line.replace('PATH=["', "").replace('"]', "").strip()
                    os.environ["PATH"] = os.environ["PATH"] + ":" + addition

    def install_tooling(self) -> None:
        self.__create_conan_profile()

        conan_install_dir = tempfile.mkdtemp()
        self.__install_protoc_via_conan(conan_install_dir)
        self.__extend_path_with_protoc_and_plugin(conan_install_dir)

    def get_binary_path(self, binary_name: str) -> str:
        path = shutil.which(binary_name)
        if path is None:
            raise KeyError(f"{binary_name!r} missing!")
        return path

    def __invoke_code_generator(
        self, proto_file_path: str, include_path: str, output_path: str
    ) -> None:
        print("Invoking gRPC code generator")
        args = [
            self.get_binary_path("protoc"),
            f"--plugin=protoc-gen-grpc={self.get_binary_path('grpc_cpp_plugin')}",
            f"-I{include_path}",
            f"--cpp_out={output_path}",
            f"--grpc_out={output_path}",
            proto_file_path,
        ]
        subprocess.check_call(
            args,
            cwd=include_path,
            env=os.environ,
            stdout=subprocess.DEVNULL if not self._verbose else None,
        )

    def generate_service_client_sdk(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        self.__invoke_code_generator(
            proto_file_handle.file_path,
            str(Path(proto_file_handle.file_path).parent),
            output_path,
        )

        conan_helper.create_conan_project(
            output_path,
            proto_file_handle.get_package(),
            proto_file_handle.get_service_name(),
        )

        conan_helper.export_conan_project(output_path)

        conan_helper.add_dependency_to_conanfile(
            f"{proto_file_handle.get_service_name().lower()}-service-sdk", "generated"
        )

    def generate_service_server_sdk(self) -> None:
        pass
