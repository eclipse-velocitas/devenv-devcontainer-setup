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

import proto
from generator import GrpcInterfaceGenerator
from util import replace_in_file, to_camel_case
from util.templates import CopySpec, copy_templates
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


class PythonGrpcInterfaceGenerator(GrpcInterfaceGenerator):  # type: ignore
    def __init__(self, verbose: bool):
        self._verbose = verbose

    def install_tooling(self) -> None:
        subprocess.check_call(["pip", "install", "grpcio-tools"])

    def __invoke_code_generator(
        self, proto_file_handle: proto.ProtoFileHandle, output_path: str
    ) -> None:
        subprocess.check_call(
            [
                "python",
                "-m",
                "grpc_tools.protoc",
                f"-I{Path(proto_file_handle.file_path).parent}",
                f"--python_out={output_path}",
                f"--pyi_out={output_path}",
                f"--grpc_python_out={output_path}",
                proto_file_handle.file_path,
            ]
        )

    def __copy_code_and_templates(self, output_path: str, service_name: str) -> None:
        module_name = f"{service_name.lower()}_service_sdk"
        source_path = os.path.join(output_path, module_name)
        os.makedirs(os.path.join(output_path, source_path), exist_ok=True)

        generated_sources = glob.glob(os.path.join(output_path, "*.py*"))
        replace_in_file(
            os.path.join(output_path, f"{service_name.lower()}_pb2_grpc.py"),
            f"import {service_name.lower()}_pb2",
            f"import {module_name}.{service_name.lower()}_pb2",
        )

        for file in generated_sources:
            shutil.move(file, source_path)

        files_to_copy = [
            CopySpec(
                source_path="ServiceNameServiceClientFactory.py",
                target_path=os.path.join(
                    source_path, f"{service_name}ServiceClientFactory.py"
                ),
            ),
            CopySpec(source_path="pyproject.toml"),
        ]

        variables = {
            "service_name": service_name,
            "service_name_lower": service_name.lower(),
            "service_name_camel_case": to_camel_case(service_name),
            "core_sdk_version": get_required_sdk_version_python(),
        }

        template_dir = os.path.join(
            get_package_path(),
            "grpc-interface-support",
            "templates",
            "python",
        )

        copy_templates(template_dir, output_path, files_to_copy, variables)

    def __install_module(self, module_path: str) -> None:
        subprocess.check_call(["pip", "install", module_path])

    def generate_service_client_sdk(
        self, output_path: str, proto_file_handle: proto.ProtoFileHandle
    ) -> None:
        self.__invoke_code_generator(proto_file_handle, output_path)
        self.__copy_code_and_templates(
            output_path, proto_file_handle.get_service_name()
        )
        self.__install_module(output_path)

    def generate_service_server_sdk(self) -> None:
        pass
