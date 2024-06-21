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

import argparse
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import proto
from cpp import CppGrpcServiceSdkGeneratorFactory
from generator import GrpcServiceSdkGeneratorFactory
from python import PythonGrpcServiceSdkGeneratorFactory
from velocitas_lib import (
    get_programming_language,
    get_project_cache_dir,
    obtain_local_file_path,
)
from velocitas_lib.functional_interface import get_interfaces_for_type
from velocitas_lib.text_utils import create_truncated_string

DEPENDENCY_TYPE_KEY = "grpc-interface"


def create_service_sdk_dir(proto_file_handle: proto.ProtoFileHandle) -> str:
    """Create a directory for the service SDK.

    Args:
        proto_file_handle (proto.ProtoFileHandle):
            A handle to the proto file of the service.

    Returns:
        str: The absolute path to the SDK directory.
    """
    service_name = proto_file_handle.get_service_name()
    service_sdk_path = os.path.join(
        get_project_cache_dir(), "services", service_name.lower()
    )
    if os.path.isdir(service_sdk_path):
        shutil.rmtree(service_sdk_path)
    os.makedirs(service_sdk_path, exist_ok=True)

    return service_sdk_path


def generate_single_service(
    factory: GrpcServiceSdkGeneratorFactory, if_config: Dict[str, Any]
) -> None:
    """Generate an SDK for a single service.

    Args:
        factory (GrpcPackageGeneratorFactory):
            The factory from which to generate an SDK generator for a single service.
        if_config (Dict[str, Any]): The grpc-interface config.
    """
    print(
        f"Generating service SDK for {create_truncated_string(if_config['src'], 100)!r}"
    )
    proto_file_handle = proto.ProtoFileHandle(obtain_local_file_path(if_config["src"]))
    service_sdk_dir = create_service_sdk_dir(proto_file_handle)

    is_client = "required" in if_config
    is_server = "provided" in if_config

    generator = factory.create_service_generator(
        service_sdk_dir,
        proto_file_handle,
        if_config.get("includeDir", str(Path(proto_file_handle.file_path).parent)),
    )
    generator.generate_package(is_client, is_server)
    generator.install_package()
    generator.update_package_references()
    if is_server:
        generator.update_auto_generated_code()


def generate_sdks(verbose: bool) -> None:
    """Generate service SDKs for all grpc-interfaces defined in the AppManifest.json.

    Args:
        verbose (bool): Enable verbose logging.
    """
    interfaces = get_interfaces_for_type(DEPENDENCY_TYPE_KEY)

    if len(interfaces) <= 0:
        return

    LANGUAGE_FACTORIES = {
        "cpp": CppGrpcServiceSdkGeneratorFactory(verbose),
        "python": PythonGrpcServiceSdkGeneratorFactory(verbose),
    }

    if get_programming_language() not in LANGUAGE_FACTORIES:
        print(
            "gRPC interface not yet supported for programming language "
            f"{get_programming_language()!r}"
        )
        return

    factory = LANGUAGE_FACTORIES[get_programming_language()]

    print("Installing tooling...")
    factory.install_tooling()

    for grpc_service in interfaces:
        if_config = grpc_service["config"]
        generate_single_service(factory, if_config)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-v", "--verbose", action="store_true")
    args = argument_parser.parse_args()
    generate_sdks(args.verbose)
