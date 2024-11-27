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

import glob
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from generator import GrpcServiceSdkGenerator, GrpcServiceSdkGeneratorFactory
from proto import ProtoFileHandle
from velocitas_lib import (
    get_package_path,
    get_workspace_dir,
)
from velocitas_lib.conan_utils import (
    add_dependency_to_conanfile,
    export_conan_project,
    get_required_sdk_version,
)
from velocitas_lib.file_utils import (
    capture_area_in_file,
    read_file,
    write_file,
)
from velocitas_lib.templates import CopySpec, copy_templates
from velocitas_lib.text_utils import (
    to_camel_case,
)

CONAN_PROFILE_NAME = "host"


def get_template_dir() -> str:
    return os.path.join(
        get_package_path(), "grpc-interface-support", "data", "templates", "cpp"
    )


class GrpcCodeExtractor:
    """
    Provides methods for extracting code from generated gRPC c++ files.
    """

    def __init__(self, proto_file: ProtoFileHandle, base_path: str):
        self.__proto_file = proto_file
        self.__base_path = base_path

    def get_header_stub_code(self, include_path: str = ".") -> List[str]:
        grpc_header_path = os.path.join(
            self.__base_path,
            include_path,
            f"{Path(self.__proto_file.file_path).stem}.grpc.pb.h",
        )

        header_content: List[str] = capture_area_in_file(
            open(grpc_header_path, encoding="utf-8"),
            "virtual ~Service();",
            "};",
        )
        return header_content

    def get_source_stub_code(self, source_path: str = ".") -> List[str]:
        grpc_source_path = os.path.join(
            self.__base_path,
            source_path,
            f"{Path(self.__proto_file.file_path).stem}.grpc.pb.cc",
        )

        service_name = self.__proto_file.get_service_name()

        package_pieces = self.__proto_file.get_package().split(".")

        source_content: List[str] = capture_area_in_file(
            open(grpc_source_path, encoding="utf-8"),
            f"{service_name}::Service::~Service() {{",
            f"}}  // namespace {package_pieces[0]}",
        )

        # skip initial 2 lines b/c they are always empty
        return source_content[2 : len(source_content) - 2]


class CppGrpcServiceSdkGenerator(GrpcServiceSdkGenerator):  # type: ignore
    def __init__(
        self,
        package_directory_path: str,
        proto_file_handle: ProtoFileHandle,
        verbose: bool,
        proto_include_path: str,
    ):
        self.__package_directory_path = package_directory_path
        self.__proto_file_handle = proto_file_handle
        self.__verbose = verbose
        self.__proto_include_path = proto_include_path
        self.__proto_include_rel_path = os.path.relpath(
            str(Path(self.__proto_file_handle.file_path).parent),
            self.__proto_include_path,
        )
        self.__service_name = self.__proto_file_handle.get_service_name()
        self.__service_name_lower = self.__service_name.lower()
        self.__output_path = os.path.join(
            self.__package_directory_path,
            os.path.relpath(
                str(Path(self.__proto_file_handle.file_path).parent),
                self.__proto_include_path,
            ),
        )

    def __get_binary_path(self, binary_name: str) -> str:
        path = shutil.which(binary_name)
        if path is None:
            raise KeyError(f"{binary_name!r} missing!")
        return path

    def __invoke_code_generator(self) -> None:
        print("Invoking gRPC code generator")
        args = [
            self.__get_binary_path("protoc"),
            f"--plugin=protoc-gen-grpc={self.__get_binary_path('grpc_cpp_plugin')}",
            f"-I{self.__proto_include_path}",
            f"--cpp_out={self.__package_directory_path}",
            f"--grpc_out={self.__package_directory_path}",
            self.__proto_file_handle.file_path,
        ]
        subprocess.check_call(
            args,
            cwd=self.__proto_include_path,
            env=os.environ,
            stdout=subprocess.DEVNULL if not self.__verbose else None,
        )

        imports = self.__proto_file_handle.get_imports()

        for element in imports:
            path = os.path.join(self.__proto_include_path, element)
            args = [
                self.__get_binary_path("protoc"),
                f"-I{self.__proto_include_path}",
                f"--cpp_out={self.__package_directory_path}",
                path,
            ]
            subprocess.check_call(
                args,
                cwd=self.__proto_include_path,
                env=os.environ,
                stdout=subprocess.DEVNULL if not self.__verbose else None,
            )

    def generate_package(self, client_required: bool, server_required: bool) -> None:
        self.__invoke_code_generator()

        files_to_copy: List[CopySpec] = []

        if client_required:
            files_to_copy.extend(self.__get_service_client_files(self.__service_name))

        if server_required:
            files_to_copy.extend(self.__get_service_server_files(self.__service_name))

        copy_templates(
            get_template_dir(),
            self.__package_directory_path,
            files_to_copy,
            self.__get_template_variables(),
        )

    def __get_template_variables(self) -> Dict[str, str]:
        return {
            "service_name": self.__service_name,
            "service_name_lower": self.__service_name_lower,
            "service_name_camel_case": to_camel_case(self.__service_name),
            "package_id": self.__proto_file_handle.get_package().replace(".", "::"),
            "core_sdk_version": str(get_required_sdk_version()),
            "service_include_dir": self.__get_relative_file_dir(),
            "proto_location": self.__proto_include_rel_path,
            "grpc_service_header_path": os.path.join(
                self.__get_relative_file_dir(),
                f"{Path(self.__proto_file_handle.file_path).stem}.grpc.pb.h",
            ),
        }

    def __get_relative_file_dir(self) -> str:
        rel_path = self.__proto_include_rel_path
        if rel_path == ".":
            return f"services/{self.__proto_file_handle.get_service_name().lower()}"

        return (
            f"services/{self.__proto_file_handle.get_service_name().lower()}/{rel_path}"
        )

    def __get_include_dir(self) -> str:
        return f"include/{self.__get_relative_file_dir()}"

    def __get_source_dir(self) -> str:
        return f"src/{self.__get_relative_file_dir()}"

    def __get_service_client_files(self, service_name: str) -> List[CopySpec]:
        return [
            CopySpec(
                "ServiceNameServiceClientFactory.h",
                f"{self.__get_include_dir()}/{to_camel_case(service_name)}ServiceClientFactory.h",
            ),
            CopySpec(
                "ServiceNameServiceClientFactory.cc",
                f"{self.__get_source_dir()}/{to_camel_case(service_name)}ServiceClientFactory.cc",
            ),
        ]

    def __get_service_server_files(self, service_name: str) -> List[CopySpec]:
        return [
            CopySpec(
                "ServiceNameServiceServerFactory.h",
                f"{self.__get_include_dir()}/{to_camel_case(service_name)}ServiceServerFactory.h",
            ),
            CopySpec(
                "ServiceNameServiceServerFactory.cc",
                f"{self.__get_source_dir()}/{to_camel_case(service_name)}ServiceServerFactory.cc",
            ),
        ]

    def __move_generated_sources(
        self,
        output_dir: str,
        include_dir_rel: str,
        src_dir_rel: str,
    ) -> Tuple[List[str], List[str]]:
        """Move generated source code from the generation dir into
        headers: <output_dir>/<include_dir_rel>
        sources: <output_dir>/<src_dir_rel>
        Args:
            generated_source_dir (str): The directory containing the generated sources.
            output_dir (str): The root directory to move the generated files to.
            include_dir_rel (str): Path relative to output_dir where to move the headers to.
            src_dir_rel (str): Path relative to the output_dir where to move the sources to.
            @@ -57,19 +57,19 @@ def move_generated_sources(
                [1] = a list of the paths to all sources
        """

        headers = glob.glob(os.path.join(self.__output_path, "*.h"))
        sources = glob.glob(os.path.join(self.__output_path, "*.cc"))

        headers_relative = []
        for header in headers:
            header_path = os.path.join(output_dir, include_dir_rel)
            os.makedirs(header_path, exist_ok=True)
            shutil.move(header, header_path)
            headers_relative.append(
                os.path.join(include_dir_rel, os.path.basename(header))
            )

        sources_relative = []
        for source in sources:
            source_path = os.path.join(output_dir, src_dir_rel)
            os.makedirs(source_path, exist_ok=True)
            shutil.move(source, source_path)
            sources_relative.append(os.path.join(src_dir_rel, os.path.basename(source)))

        return headers_relative, sources_relative

    def install_package(self) -> None:
        proto_headers, proto_sources = self.__move_generated_sources(
            self.__package_directory_path,
            self.__get_include_dir(),
            self.__get_source_dir(),
        )

        files_to_copy = [
            CopySpec(source_path="CMakeLists.txt"),
            CopySpec(source_path="conanfile.py"),
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
        variables["proto_headers"] = "\n\t".join(proto_headers)
        variables["proto_sources"] = "\n\t".join(proto_sources)

        copy_templates(
            get_template_dir(),
            self.__package_directory_path,
            files_to_copy,
            variables,
        )

        export_conan_project(self.__package_directory_path)

    def __transform_header_stub_code(self, lines: List[str]) -> List[str]:
        service_class_name = to_camel_case(self.__service_name) + "Service"

        result: List[str] = []

        for line in lines:
            line = line.rstrip().replace("Service", service_class_name)
            if line.lstrip().startswith("virtual"):
                result.append(line.replace("virtual ", "").replace(";", " override;"))

        return result

    def __transform_source_stub_code(self, lines: List[str]) -> List[str]:
        service_class_name = to_camel_case(self.__service_name) + "Service"

        result: List[str] = []

        for line in lines:
            result.append(
                line.replace(f"{self.__service_name}::Service", service_class_name)
            )

        return result

    def __create_or_update_service_header(self) -> None:
        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = f"{to_camel_case(self.__service_name)}ServiceImpl.h"
        service_header_file_path = os.path.join(
            app_source_dir, service_header_file_name
        )

        if os.path.exists(service_header_file_path):
            self.__update_service_header()
        else:
            self.__create_service_header()

    def __create_service_header(self) -> None:
        header_stub_code = GrpcCodeExtractor(
            self.__proto_file_handle, self.__package_directory_path
        ).get_header_stub_code(self.__get_include_dir())

        header_stub_code = self.__transform_header_stub_code(header_stub_code)

        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = f"{to_camel_case(self.__service_name)}ServiceImpl.h"
        variables = self.__get_template_variables()
        variables["service_header_code"] = "\n".join(header_stub_code)

        copy_templates(
            get_template_dir(),
            app_source_dir,
            [CopySpec("ServiceImpl.h", service_header_file_name)],
            variables,
        )

    def __update_service_header(self) -> None:
        header_generated_code = GrpcCodeExtractor(
            self.__proto_file_handle, self.__package_directory_path
        ).get_header_stub_code(self.__get_include_dir())

        header_generated_code = self.__transform_header_stub_code(header_generated_code)

        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_header_file_name = f"{to_camel_case(self.__service_name)}ServiceImpl.h"
        service_header_file_path = os.path.join(
            app_source_dir, service_header_file_name
        )

        auto_generated_code = capture_area_in_file(
            open(service_header_file_path, encoding="utf-8"),
            "// <auto-generated>",
            "// </auto-generated>",
        )

        header_file_content = read_file(service_header_file_path)
        modified_content = header_file_content.replace(
            "\n".join(auto_generated_code), "\n".join(header_generated_code)
        )
        write_file(service_header_file_path, modified_content)

    def __create_service_source(self) -> None:
        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_source_file_name = (
            f"{to_camel_case(self.__service_name)}ServiceImpl.cpp"
        )
        service_source_file_path = os.path.join(
            app_source_dir, service_source_file_name
        )

        if os.path.exists(service_source_file_path):
            return

        source_code = GrpcCodeExtractor(
            self.__proto_file_handle, self.__package_directory_path
        ).get_source_stub_code(self.__get_source_dir())

        source_code = self.__transform_source_stub_code(source_code)

        variables = self.__get_template_variables()
        variables["service_source_code"] = "\n".join(source_code)

        copy_templates(
            get_template_dir(),
            app_source_dir,
            [CopySpec("ServiceImpl.cpp", service_source_file_path)],
            variables,
        )

    def update_package_references(self) -> None:
        """Update all references to the generated package."""

        add_dependency_to_conanfile(
            f"{self.__service_name_lower}-service-sdk",
            "generated",
        )

    def update_auto_generated_code(self) -> None:
        self.__create_or_update_service_header()
        self.__create_service_source()


class CppGrpcServiceSdkGeneratorFactory(GrpcServiceSdkGeneratorFactory):  # type: ignore
    def __init__(self, verbose: bool):
        self._verbose = verbose

    def create_service_generator(
        self,
        output_path: str,
        proto_file_handle: ProtoFileHandle,
        proto_include_path: str,
    ) -> GrpcServiceSdkGenerator:
        return CppGrpcServiceSdkGenerator(
            output_path, proto_file_handle, self._verbose, proto_include_path
        )

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

        deps_to_extract = [
            "grpc",
            "c-ares",
            "googleapis",
            "grpc-proto",
            "zlib",
            "protobuf",
            "openssl",
        ]
        deps_patterns = [
            re.compile(r"^.*\"(" + dep + r"\/.*)\".*$") for dep in deps_to_extract
        ]
        deps_results = []
        with open(
            os.path.join(get_template_dir(), "conanfile.py"), encoding="utf-8"
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
