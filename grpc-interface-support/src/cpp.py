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
from io import TextIOWrapper
from pathlib import Path
from typing import Callable, Dict, List, Optional

import shared_utils
from generator import GrpcServiceSdkGenerator, GrpcServiceSdkGeneratorFactory
from proto import ProtoFileHandle
from shared_utils import conan_helper, templates
from velocitas_lib import get_package_path, get_workspace_dir

CONAN_PROFILE_NAME = "host"


def capture_textfile_area(
    file: TextIOWrapper,
    start_line: str,
    end_line: str,
    map_fn: Optional[Callable[[str], str]] = None,
) -> List[str]:
    area_content: List[str] = []
    is_capturing = False
    for line in file:
        if line.strip() == start_line:
            is_capturing = True
        elif line.strip() == end_line:
            is_capturing = False
        elif is_capturing:
            line = line.rstrip()

            if map_fn:
                line = map_fn(line)

            area_content.append(line)
    return area_content


class GrpcCodeExtractor:
    """
    Provides methods for extracing code from generated gRPC c++ files.
    """

    def __init__(self, proto_file: ProtoFileHandle, base_path: str):
        self.__proto_file = proto_file
        self.__base_path = base_path

    def get_header_stub_code(self, include_path: str = ".") -> List[str]:
        grpc_header_path = os.path.join(
            self.__base_path,
            include_path,
            f"{self.__proto_file.get_service_name().lower()}.grpc.pb.h",
        )

        header_content = capture_textfile_area(
            open(grpc_header_path, encoding="utf-8"),
            "virtual ~Service();",
            "};",
        )
        return header_content

    def get_source_stub_code(self, source_path: str = ".") -> List[str]:
        grpc_source_path = os.path.join(
            self.__base_path,
            source_path,
            f"{self.__proto_file.get_service_name().lower()}.grpc.pb.cc",
        )

        service_name = shared_utils.to_camel_case(self.__proto_file.get_service_name())

        package_pieces = self.__proto_file.get_package().split(".")

        source_content = capture_textfile_area(
            open(grpc_source_path, encoding="utf-8"),
            f"{service_name}::Service::~Service() {{",
            f"}}  // namespace {package_pieces[0]}",
        )

        return source_content[2 : len(source_content) - 2]


class CppGrpcServiceSdkGenerator(GrpcServiceSdkGenerator):  # type: ignore
    def __init__(
        self,
        package_directory_path: str,
        proto_file_handle: ProtoFileHandle,
        verbose: bool,
    ):
        self.__package_directory_path = package_directory_path
        self.__proto_file_handle = proto_file_handle
        self.__verbose = verbose

    def __get_binary_path(self, binary_name: str) -> str:
        path = shutil.which(binary_name)
        if path is None:
            raise KeyError(f"{binary_name!r} missing!")
        return path

    def __invoke_code_generator(self, include_path: str, output_path: str) -> None:
        print("Invoking gRPC code generator")
        args = [
            self.__get_binary_path("protoc"),
            f"--plugin=protoc-gen-grpc={self.__get_binary_path('grpc_cpp_plugin')}",
            f"-I{include_path}",
            f"--cpp_out={output_path}",
            f"--grpc_out={output_path}",
            self.__proto_file_handle.file_path,
        ]
        subprocess.check_call(
            args,
            cwd=include_path,
            env=os.environ,
            stdout=subprocess.DEVNULL if not self.__verbose else None,
        )

    def generate_package(self, client_required: bool, server_required: bool) -> None:
        self.__invoke_code_generator(
            str(Path(self.__proto_file_handle.file_path).parent),
            self.__package_directory_path,
        )

        if client_required:
            self.__generate_service_client()

        if server_required:
            self.__generate_service_server()

    def __get_template_variables(self) -> Dict[str, str]:
        service_name = self.__proto_file_handle.get_service_name()

        return {
            "service_name": service_name,
            "service_name_lower": service_name.lower(),
            "service_name_camel_case": shared_utils.to_camel_case(service_name),
            "package_id": self.__proto_file_handle.get_package().replace(".", "::"),
            "core_sdk_version": str(conan_helper.get_required_sdk_version()),
        }

    def __get_template_dir(self) -> str:
        return os.path.join(
            get_package_path(), "grpc-interface-support", "templates", "cpp"
        )

    def __get_relative_include_dir(self) -> str:
        return f"services/{self.__proto_file_handle.get_service_name().lower()}"

    def __get_include_dir(self) -> str:
        return f"include/{self.__get_relative_include_dir()}"

    def __get_source_dir(self) -> str:
        return f"src/services/{self.__proto_file_handle.get_service_name().lower()}"

    def __generate_service_client(self) -> None:
        service_name = self.__proto_file_handle.get_service_name()

        files_to_copy = [
            templates.CopySpec(
                "ServiceNameServiceClientFactory.h",
                f"{self.__get_include_dir()}/{shared_utils.to_camel_case(service_name)}ServiceClientFactory.h",
            ),
            templates.CopySpec(
                "ServiceNameServiceClientFactory.cc",
                f"{self.__get_source_dir()}/{shared_utils.to_camel_case(service_name)}ServiceClientFactory.cc",
            ),
        ]

        templates.copy_templates(
            self.__get_template_dir(),
            self.__package_directory_path,
            files_to_copy,
            self.__get_template_variables(),
        )

    def __generate_service_server(self) -> None:
        service_name = self.__proto_file_handle.get_service_name()

        files_to_copy = [
            templates.CopySpec(
                "ServiceNameServiceServerFactory.h",
                f"{self.__get_include_dir()}/{shared_utils.to_camel_case(service_name)}ServiceServerFactory.h",
            ),
            templates.CopySpec(
                "ServiceNameServiceServerFactory.cc",
                f"{self.__get_source_dir()}/{shared_utils.to_camel_case(service_name)}ServiceServerFactory.cc",
            ),
        ]

        templates.copy_templates(
            self.__get_template_dir(),
            self.__package_directory_path,
            files_to_copy,
            self.__get_template_variables(),
        )

    def install_package(self) -> None:
        conan_helper.move_generated_sources(
            self.__package_directory_path,
            self.__package_directory_path,
            self.__get_include_dir(),
            self.__get_source_dir(),
        )

        files_to_copy = [
            templates.CopySpec(source_path="CMakeLists.txt"),
            templates.CopySpec(source_path="conanfile.py"),
        ]

        variables = self.__get_template_variables()

        cmake_headers = [
            os.path.join(self.__get_include_dir(), file)
            for file in os.listdir(
                os.path.join(self.__package_directory_path, self.__get_include_dir())
            )
        ]

        cmake_sources = [
            os.path.join(self.__get_source_dir(), file)
            for file in os.listdir(
                os.path.join(self.__package_directory_path, self.__get_source_dir())
            )
        ]

        variables["cmake_headers"] = "\n\t".join(cmake_headers)
        variables["cmake_sources"] = "\n\t".join(cmake_sources)

        templates.copy_templates(
            self.__get_template_dir(),
            self.__package_directory_path,
            files_to_copy,
            variables,
        )

        conan_helper.export_conan_project(self.__package_directory_path)

    def __transform_header_stub_code(self, lines: List[str]) -> List[str]:
        service_name = self.__proto_file_handle.get_service_name()
        service_class_name = shared_utils.to_camel_case(service_name) + "Service"

        result: List[str] = []

        for line in lines:
            line = line.rstrip().replace("Service", service_class_name)
            service_class_name = service_name + "Service"
            if line.lstrip().startswith("virtual"):
                result.append(line.replace("virtual ", "").replace(";", " override;"))

        return result

    def __transform_source_stub_code(self, lines: List[str]) -> List[str]:
        service_name = self.__proto_file_handle.get_service_name()
        service_class_name = shared_utils.to_camel_case(service_name) + "Service"

        result: List[str] = []

        for line in lines:
            result.append(line.replace(f"{service_name}::Service", service_class_name))

        return result

    def __create_or_update_service_header(self) -> None:
        header_stub_code = GrpcCodeExtractor(
            self.__proto_file_handle, self.__package_directory_path
        ).get_header_stub_code(self.__get_include_dir())

        header_stub_code = self.__transform_header_stub_code(header_stub_code)

        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = (
            f"{self.__proto_file_handle.get_service_name()}ServiceImpl.h"
        )
        service_header_file_path = os.path.join(
            app_source_dir, service_header_file_name
        )

        user_defined_code: List[str] = []
        if os.path.exists(service_header_file_path):
            # there is a previous version of the header
            # extract the user-defined code

            user_defined_code = capture_textfile_area(
                open(service_header_file_path, encoding="utf-8"),
                "// <user-defined>",
                "// </user-defined>",
            )

        variables = self.__get_template_variables()
        variables["service_header_code"] = "\n".join(header_stub_code)
        variables["grpc_service_header_path"] = os.path.join(
            self.__get_relative_include_dir(),
            f"{self.__proto_file_handle.get_service_name().lower()}.grpc.pb.h",
        )
        variables["service_header_user_code"] = "\n".join(user_defined_code)

        # file does not exist it, copy over the template
        templates.copy_templates(
            self.__get_template_dir(),
            app_source_dir,
            [templates.CopySpec("ServiceImpl.h", service_header_file_name)],
            variables,
        )

    def __create_service_source(self) -> None:
        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = (
            f"{self.__proto_file_handle.get_service_name()}ServiceImpl.cpp"
        )
        service_header_file_path = os.path.join(
            app_source_dir, service_header_file_name
        )

        if os.path.exists(service_header_file_path):
            return

        source_code = GrpcCodeExtractor(
            self.__proto_file_handle, self.__package_directory_path
        ).get_source_stub_code(self.__get_source_dir())

        source_code = self.__transform_source_stub_code(source_code)

        variables = self.__get_template_variables()
        variables["service_source_code"] = "\n".join(source_code)

        templates.copy_templates(
            self.__get_template_dir(),
            app_source_dir,
            [templates.CopySpec("ServiceImpl.cpp", service_header_file_name)],
            variables,
        )

    def update_package_references(self) -> None:
        """Update all references to the generated package."""

        conan_helper.add_dependency_to_conanfile(
            f"{self.__proto_file_handle.get_service_name().lower()}-service-sdk",
            "generated",
        )

    def update_auto_generated_code(self) -> None:
        self.__create_or_update_service_header()
        self.__create_service_source()


class CppGrpcServiceSdkGeneratorFactory(GrpcServiceSdkGeneratorFactory):  # type: ignore
    def __init__(self, verbose: bool):
        self._verbose = verbose

    def create_service_generator(
        self, output_path: str, proto_file_handle: ProtoFileHandle
    ) -> GrpcServiceSdkGenerator:
        return CppGrpcServiceSdkGenerator(output_path, proto_file_handle, self._verbose)

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
