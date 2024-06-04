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
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import proto
from generator import GrpcServiceSdkGenerator, GrpcServiceSdkGeneratorFactory
from proto import ProtoFileHandle
from shared_utils import (
    capture_textfile_area,
    replace_in_file,
    replace_line,
    replace_text_area,
    templates,
    to_camel_case,
)
from shared_utils.templates import CopySpec, copy_templates
from velocitas_lib import get_package_path, get_workspace_dir


def get_required_sdk_version_python() -> str:
    sdk_version: str = "0.11.0"
    with open(
        os.path.join(get_workspace_dir(), "app", "requirements.txt"), encoding="utf-8"
    ) as requirements_file:
        for line in requirements_file:
            if line.startswith("vehicle-app-sdk"):
                sdk_version = line.split("==")[1].strip()

    return sdk_version


def get_template_dir() -> str:
    return os.path.join(
        get_package_path(), "grpc-interface-support", "data", "templates", "python"
    )


class GrpcCodeExtractor:
    """
    Provides methods for extracting code from generated gRPC python files.
    """

    def __init__(
        self, proto_file: ProtoFileHandle, base_path: str, source_path: str = "."
    ):
        self.__proto_file = proto_file
        self.__base_path = base_path
        self.__source_path = source_path

        self.grpc_source_path = os.path.join(
            self.__base_path,
            self.__source_path,
            f"{self.__proto_file.get_service_name().lower()}_pb2_grpc.py",
        )

    def create_source_stub_code(self) -> List[str]:
        service_name = to_camel_case(self.__proto_file.get_service_name())

        source_content: List[str] = capture_textfile_area(
            open(self.grpc_source_path, encoding="utf-8"),
            f"class {service_name}Servicer(object):",
            f"def add_{service_name}Servicer_to_server(servicer, server):",
        )

        # Remove leading whitespaces because they do not match the expected python intendation
        if len(source_content) > 0:
            source_content[0] = source_content[0].lstrip()

        return source_content


class PythonGrpcInterfaceGenerator(GrpcServiceSdkGenerator):  # type: ignore
    TEMPLATE_PATH = "ServiceImpl.py"

    def __init__(
        self,
        package_directory_path: str,
        proto_file_handle: proto.ProtoFileHandle,
        verbose: bool,
    ):
        self.__package_directory_path = package_directory_path
        self.__proto_file_handle = proto_file_handle
        self.__verbose = verbose
        self.__seats_grpc_code_extractor = GrpcCodeExtractor(
            self.__proto_file_handle, self.__package_directory_path, "seats_service_sdk"
        )

    def __invoke_code_generator(self) -> None:
        subprocess.check_call(
            [
                "python",
                "-m",
                "grpc_tools.protoc",
                f"-I{Path(self.__proto_file_handle.file_path).parent}",
                f"--python_out={self.__package_directory_path}",
                f"--pyi_out={self.__package_directory_path}",
                f"--grpc_python_out={self.__package_directory_path}",
                self.__proto_file_handle.file_path,
            ]
        )

    def __copy_code_and_templates(
        self, client_required: bool, server_required: bool
    ) -> None:
        service_name = self.__proto_file_handle.get_service_name()
        module_name = f"{service_name.lower()}_service_sdk"
        source_path = os.path.join(self.__package_directory_path, module_name)
        os.makedirs(
            os.path.join(self.__package_directory_path, source_path), exist_ok=True
        )

        generated_sources = glob.glob(
            os.path.join(self.__package_directory_path, "*.py*")
        )
        replace_in_file(
            os.path.join(
                self.__package_directory_path, f"{service_name.lower()}_pb2_grpc.py"
            ),
            f"import {service_name.lower()}_pb2",
            f"import {module_name}.{service_name.lower()}_pb2",
        )

        for file in generated_sources:
            shutil.move(file, source_path)

        files_to_copy: List[CopySpec] = []

        if client_required:
            files_to_copy.extend(
                [
                    CopySpec(
                        source_path="ServiceNameServiceClientFactory.py",
                        target_path=os.path.join(
                            source_path, f"{service_name}ServiceClientFactory.py"
                        ),
                    ),
                    CopySpec(source_path="pyproject.toml"),
                ]
            )

        if server_required:
            files_to_copy.extend(
                [
                    CopySpec(
                        source_path="ServiceNameServiceServerFactory.py",
                        target_path=os.path.join(
                            source_path, f"{service_name}ServiceServerFactory.py"
                        ),
                    ),
                    CopySpec(source_path="pyproject.toml"),
                ]
            )

        variables = {
            "service_name": service_name,
            "service_name_lower": service_name.lower(),
            "service_name_camel_case": to_camel_case(service_name),
            "core_sdk_version": get_required_sdk_version_python(),
        }

        template_dir = os.path.join(
            get_package_path(),
            "grpc-interface-support",
            "data",
            "templates",
            "python",
        )

        copy_templates(
            template_dir, self.__package_directory_path, files_to_copy, variables
        )

    def __create_stub_source(self) -> None:
        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")

        source_code = self.__seats_grpc_code_extractor.create_source_stub_code()
        variables = self.__create_stub_template_variables()
        variables["service_source_code"] = "\n".join(source_code)

        source_file_name = (
            f"{self.__proto_file_handle.get_service_name()}ServiceStub.py"
        )
        source_file_path = os.path.join(app_source_dir, source_file_name)
        templates.copy_templates(
            get_template_dir(),
            app_source_dir,
            [templates.CopySpec(self.TEMPLATE_PATH, source_file_path)],
            variables,
        )

    def __create_service_source(self) -> None:
        app_source_dir = os.path.join(get_workspace_dir(), "app", "src")
        service_source_file_name = (
            f"{self.__proto_file_handle.get_service_name()}{self.TEMPLATE_PATH}"
        )
        service_source_file_path = os.path.join(
            app_source_dir, service_source_file_name
        )

        if os.path.exists(service_source_file_path):
            return

        source_code = self.__seats_grpc_code_extractor.create_source_stub_code()
        source_code = self.__transform_service_source_code(source_code)

        variables = self.__create_service_template_variables()
        variables["service_source_code"] = "\n".join(source_code)

        templates.copy_templates(
            get_template_dir(),
            app_source_dir,
            [templates.CopySpec("ServiceImpl.py", service_source_file_path)],
            variables,
        )

    def __transform_service_source_code(self, lines: List[str]) -> List[str]:
        source_content = replace_text_area(
            lines,
            '"""',
            '"""',
        )
        source_content = replace_line(
            source_content,
            "context.set",
        )

        return source_content

    def __create_stub_template_variables(self) -> Dict[str, str]:
        service_name = self.__proto_file_handle.get_service_name()

        return {
            "service_name": service_name,
            "service_name_parent_postfix": "Servicer",
            "service_name_lower": service_name.lower(),
            "service_name_camel_case": to_camel_case(service_name),
            "service_name_postfix": "Stub",
            "package_id": "seats_service_sdk.seats_pb2_grpc",
        }

    def __create_service_template_variables(self) -> Dict[str, str]:
        service_name = self.__proto_file_handle.get_service_name()

        return {
            "service_name": "SeatsServiceStub",
            "service_name_parent_postfix": "",
            "service_name_lower": service_name.lower(),
            "service_name_camel_case": to_camel_case(service_name),
            "service_name_postfix": "",
            "package_id": "SeatsServiceStub",
        }

    def __install_module(self) -> None:
        subprocess.check_call(["pip", "install", self.__package_directory_path])

    def generate_package(
        self,
        client_required: bool,
        server_required: bool,
    ) -> None:
        self.__invoke_code_generator()
        self.__copy_code_and_templates(client_required, server_required)

    def install_package(self) -> None:
        self.__install_module()

    def update_package_references(self) -> None:
        pass

    def update_auto_generated_code(self) -> None:
        self.__create_stub_source()
        self.__create_service_source()


class PythonGrpcServiceSdkGeneratorFactory(GrpcServiceSdkGeneratorFactory):  # type: ignore
    def __init__(self, verbose: bool):
        self._verbose = verbose

    def install_tooling(self) -> None:
        subprocess.check_call(["pip", "install", "grpcio-tools"])

    def create_service_generator(
        self, output_path: str, proto_file_handle: proto.ProtoFileHandle
    ) -> PythonGrpcInterfaceGenerator:
        return PythonGrpcInterfaceGenerator(
            output_path, proto_file_handle, self._verbose
        )
