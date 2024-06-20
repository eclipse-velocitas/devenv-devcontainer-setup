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
from typing import List

import proto
from generator import GrpcServiceSdkGenerator, GrpcServiceSdkGeneratorFactory
from velocitas_lib import (
    get_package_path,
    get_workspace_dir,
)
from velocitas_lib.templates import CopySpec, copy_templates
from velocitas_lib.text_utils import replace_text_in_file, to_camel_case


def get_required_sdk_version_python() -> str:
    sdk_version: str = "0.11.0"
    with open(
        os.path.join(get_workspace_dir(), "app", "requirements.txt"), encoding="utf-8"
    ) as requirements_file:
        for line in requirements_file:
            if line.startswith("vehicle-app-sdk"):
                sdk_version = line.split("==")[1].strip()

    return sdk_version


class PythonGrpcInterfaceGenerator(GrpcServiceSdkGenerator):  # type: ignore
    def __init__(
        self,
        package_directory_path: str,
        proto_file_handle: proto.ProtoFileHandle,
        verbose: bool,
        proto_include_path: str,
    ):
        self.__package_directory_path = package_directory_path
        self.__proto_file_handle = proto_file_handle
        self.__verbose = verbose
        self.__proto_include_path = proto_include_path

    def __invoke_code_generator(self) -> None:
        subprocess.check_call(
            [
                "python",
                "-m",
                "grpc_tools.protoc",
                f"-I{self.__proto_include_path}",
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
        replace_text_in_file(
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
            print("WARN: Server generation not supported yet for Python!")

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
        pass


class PythonGrpcServiceSdkGeneratorFactory(GrpcServiceSdkGeneratorFactory):  # type: ignore
    def __init__(self, verbose: bool):
        self._verbose = verbose

    def install_tooling(self) -> None:
        subprocess.check_call(["pip", "install", "grpcio-tools"])

    def create_service_generator(
        self,
        output_path: str,
        proto_file_handle: proto.ProtoFileHandle,
        proto_include_path: str,
    ) -> PythonGrpcInterfaceGenerator:
        return PythonGrpcInterfaceGenerator(
            output_path, proto_file_handle, self._verbose, proto_include_path
        )
