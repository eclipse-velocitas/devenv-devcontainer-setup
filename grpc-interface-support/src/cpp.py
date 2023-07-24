# Copyright (c) 2023 Contributors to the Eclipse Foundation
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
from typing import Optional

import conan_helper
from generator import GrpcInterfaceGenerator
from proto import ProtoFileHandle
from velocitas_lib import get_package_path

CONAN_PROFILE_NAME = "host"


class CppGrpcInterfaceGenerator(GrpcInterfaceGenerator):  # type: ignore
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
            stdout=subprocess.DEVNULL,
        )

    def __install_protoc_via_conan(self, conan_build_dir: str) -> None:
        env = os.environ.copy()
        env["CONAN_REVISIONS_ENABLED"] = "1"

        template_dir = os.path.join(
            get_package_path(), "grpc-interface-support", "templates", "cpp"
        )

        grpc_version: Optional[str] = None
        cares_version: Optional[str] = None
        grpc_pattern = re.compile(r"^.*\"(grpc\/.*)\".*$")
        cares_pattern = re.compile(r"^.*\"(c-ares\/.*)\".*$")
        with open(
            os.path.join(template_dir, "conanfile.py"), encoding="utf-8"
        ) as conanfile:
            for line in conanfile:
                match = grpc_pattern.match(line)
                if match is not None:
                    grpc_version = match.group(1)
                else:
                    match = cares_pattern.match(line)
                    if match is not None:
                        cares_version = match.group(1)

        if not grpc_version:
            raise RuntimeError("conanfile.py does not have a dependency on gRPC!")

        tmpdir = tempfile.mkdtemp()
        tooling_conanfile_path = os.path.join(tmpdir, "conanfile.txt")
        with open(
            tooling_conanfile_path, mode="w", encoding="utf-8"
        ) as tooling_conanfile:
            tooling_conanfile.write(
                f"""
[requires]
{grpc_version}
{cares_version}
"""
            )

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
            stdout=subprocess.DEVNULL,
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

    def get_protoc_binary_path(self) -> str:
        path = shutil.which("protoc")
        if path is None:
            raise KeyError("protoc missing!")
        return path

    def get_protoc_cpp_plugin_binary_path(self) -> str:
        path = shutil.which("grpc_cpp_plugin")
        if path is None:
            raise KeyError("grpc_cpp_plugin is missing!")
        return path

    def __invoke_code_generator(
        self, proto_file_path: str, include_path: str, output_path: str
    ) -> None:
        print("Invoking gRPC code generator")
        args = [
            self.get_protoc_binary_path(),
            f"--plugin=protoc-gen-grpc={self.get_protoc_cpp_plugin_binary_path()}",
            f"-I{include_path}",
            f"--cpp_out={output_path}",
            f"--grpc_out={output_path}",
            proto_file_path,
        ]
        subprocess.check_call(
            args, cwd=include_path, env=os.environ, stdout=subprocess.DEVNULL
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
            f"{proto_file_handle.get_service_name().lower()}-service-sdk/auto"
        )

    def generate_service_server_sdk(self) -> None:
        pass
