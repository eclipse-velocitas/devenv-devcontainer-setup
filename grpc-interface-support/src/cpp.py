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
from typing import Dict, List

from generator import GrpcInterfaceGenerator
from proto import ProtoFileHandle
from shared_utils import conan_helper, templates
import shared_utils
from velocitas_lib import get_package_path, get_workspace_dir

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

    def __get_binary_path(self, binary_name: str) -> str:
        path = shutil.which(binary_name)
        if path is None:
            raise KeyError(f"{binary_name!r} missing!")
        return path

    def __invoke_code_generator(
        self, proto_file_path: str, include_path: str, output_path: str
    ) -> None:
        print("Invoking gRPC code generator")
        args = [
            self.__get_binary_path("protoc"),
            f"--plugin=protoc-gen-grpc={self.__get_binary_path('grpc_cpp_plugin')}",
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

    def generate_package(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        self.__invoke_code_generator(
            proto_file_handle.file_path,
            str(Path(proto_file_handle.file_path).parent),
            output_path,
        )

    def __get_template_variables(
        self, proto_file_handle: ProtoFileHandle
    ) -> Dict[str, str]:
        service_name = proto_file_handle.get_service_name()

        return {
            "service_name": service_name,
            "service_name_lower": service_name.lower(),
            "service_name_camel_case": shared_utils.to_camel_case(service_name),
            "package_id": proto_file_handle.get_package().replace(".", "::"),
            "core_sdk_version": str(conan_helper.get_required_sdk_version()),
        }

    def __get_template_dir(self) -> str:
        return os.path.join(
            get_package_path(), "grpc-interface-support", "templates", "cpp"
        )

    def __get_relative_include_dir(self, proto_file_handle: ProtoFileHandle) -> str:
        return f"services/{proto_file_handle.get_service_name().lower()}"

    def __get_include_dir(self, proto_file_handle: ProtoFileHandle) -> str:
        return f"include/{self.__get_relative_include_dir(proto_file_handle)}"

    def __get_source_dir(self, proto_file_handle: ProtoFileHandle) -> str:
        return f"src/services/{proto_file_handle.get_service_name().lower()}"

    def generate_service_client(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        service_name = proto_file_handle.get_service_name()

        files_to_copy = [
            templates.CopySpec(
                "ServiceNameServiceClientFactory.h",
                f"{self.__get_include_dir(proto_file_handle)}/{shared_utils.to_camel_case(service_name)}ServiceClientFactory.h",
            ),
            templates.CopySpec(
                "ServiceNameServiceClientFactory.cc",
                f"{self.__get_source_dir(proto_file_handle)}/{shared_utils.to_camel_case(service_name)}ServiceClientFactory.cc",
            ),
        ]

        templates.copy_templates(
            self.__get_template_dir(),
            output_path,
            files_to_copy,
            self.__get_template_variables(proto_file_handle),
        )

    def generate_service_server(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        service_name = proto_file_handle.get_service_name()

        files_to_copy = [
            templates.CopySpec(
                "ServiceNameServiceServerFactory.h",
                f"{self.__get_include_dir(proto_file_handle)}/{shared_utils.to_camel_case(service_name)}ServiceServerFactory.h",
            ),
            templates.CopySpec(
                "ServiceNameServiceServerFactory.cc",
                f"{self.__get_source_dir(proto_file_handle)}/{shared_utils.to_camel_case(service_name)}ServiceServerFactory.cc",
            ),
        ]

        templates.copy_templates(
            self.__get_template_dir(),
            output_path,
            files_to_copy,
            self.__get_template_variables(proto_file_handle),
        )

    def install_package(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        conan_helper.move_generated_sources(
            output_path,
            output_path,
            self.__get_include_dir(proto_file_handle),
            self.__get_source_dir(proto_file_handle),
        )

        files_to_copy = [
            templates.CopySpec(source_path="CMakeLists.txt"),
            templates.CopySpec(source_path="conanfile.py"),
        ]

        variables = self.__get_template_variables(proto_file_handle)

        cmake_headers = [
            os.path.join(self.__get_include_dir(proto_file_handle), file)
            for file in os.listdir(
                os.path.join(output_path, self.__get_include_dir(proto_file_handle))
            )
        ]
        cmake_sources = [
            os.path.join(self.__get_source_dir(proto_file_handle), file)
            for file in os.listdir(
                os.path.join(output_path, self.__get_source_dir(proto_file_handle))
            )
        ]

        variables["cmake_headers"] = "\n\t".join(cmake_headers)
        variables["cmake_sources"] = "\n\t".join(cmake_sources)

        templates.copy_templates(
            self.__get_template_dir(), output_path, files_to_copy, variables
        )

        conan_helper.export_conan_project(output_path)

        conan_helper.add_dependency_to_conanfile(
            f"{proto_file_handle.get_service_name().lower()}-service-sdk", "generated"
        )

        self.__generate_business_logic_stubs(output_path, proto_file_handle)

    def __get_header_stub_code(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> List[str]:
        grpc_header_path = os.path.join(
            output_path,
            self.__get_include_dir(proto_file_handle),
            f"{proto_file_handle.get_service_name().lower()}.grpc.pb.h",
        )

        header_content: List[str] = []
        service_class_name = (
            shared_utils.to_camel_case(proto_file_handle.get_service_name()) + "Service"
        )
        with open(grpc_header_path, encoding="utf-8") as grpc_header_file:
            is_capturing = False
            for line in grpc_header_file:
                if line.strip() == "virtual ~Service();":
                    is_capturing = True
                elif line.strip() == "};":
                    is_capturing = False
                elif is_capturing:
                    line = line.rstrip().replace("Service", service_class_name)
                    if line.lstrip().startswith("virtual"):
                        line = line.replace("virtual ", "").replace(";", " override;")
                    header_content.append(line)
        return header_content

    def __create_or_update_service_header(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        header_stub_code = self.__get_header_stub_code(output_path, proto_file_handle)

        variables = self.__get_template_variables(proto_file_handle)
        variables["service_header_code"] = "\n".join(header_stub_code)
        variables["grpc_service_header_path"] = os.path.join(
            self.__get_relative_include_dir(proto_file_handle),
            f"{proto_file_handle.get_service_name().lower()}.grpc.pb.h",
        )

        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = (
            f"{proto_file_handle.get_service_name()}ServiceServer.h"
        )
        service_header_file_path = os.path.join(
            app_source_dir, service_header_file_name
        )

        user_defined_code: List[str] = []
        if os.path.exists(service_header_file_path):
            # there is a previous version of the header
            # extract the user-defined code

            with open(service_header_file_path, encoding="utf-8") as file:
                capture = False
                for line in file:
                    if line.strip() == "// <user-defined>":
                        capture = True
                    elif line.strip() == "// </user-defined>":
                        capture = False
                    elif capture:
                        user_defined_code.append(line.rstrip())

                if capture:
                    print("Missing closing user-defined tag")
                    user_defined_code.clear()

        variables["service_header_user_code"] = "\n".join(user_defined_code)
        # file does not exist it, copy over the template
        templates.copy_templates(
            self.__get_template_dir(),
            app_source_dir,
            [templates.CopySpec("ServiceImpl.h", service_header_file_name)],
            variables,
        )

    def __get_source_stub_code(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> List[str]:
        grpc_source_path = os.path.join(
            output_path,
            self.__get_source_dir(proto_file_handle),
            f"{proto_file_handle.get_service_name().lower()}.grpc.pb.cc",
        )

        source_content: List[str] = []
        service_class_name = (
            shared_utils.to_camel_case(proto_file_handle.get_service_name()) + "Service"
        )
        with open(grpc_source_path, encoding="utf-8") as grpc_source_file:
            is_capturing = False
            for line in grpc_source_file:
                if line.strip() == "Seats::Service::~Service() {":
                    is_capturing = True
                elif line.strip().startswith("}  // namespace"):
                    is_capturing = False
                elif is_capturing:
                    source_content.append(
                        line.rstrip().replace("Seats::Service", service_class_name)
                    )
        return source_content[2 : len(source_content) - 2]

    def __create_service_source(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        source_code = self.__get_source_stub_code(output_path, proto_file_handle)

        variables = self.__get_template_variables(proto_file_handle)
        variables["service_source_code"] = "\n".join(source_code)

        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = (
            f"{proto_file_handle.get_service_name()}ServiceServer.cpp"
        )
        service_header_file_path = os.path.join(
            app_source_dir, service_header_file_name
        )

        if os.path.exists(service_header_file_path):
            return

        templates.copy_templates(
            self.__get_template_dir(),
            app_source_dir,
            [templates.CopySpec("ServiceImpl.cpp", service_header_file_name)],
            variables,
        )

    def __generate_business_logic_stubs(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> None:
        self.__create_or_update_service_header(output_path, proto_file_handle)
        self.__create_service_source(output_path, proto_file_handle)
