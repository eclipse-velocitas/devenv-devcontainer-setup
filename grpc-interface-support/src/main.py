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
from typing import Any, Dict

import proto
from cpp import CppGrpcInterfaceGenerator
from generator import GrpcInterfaceGenerator
from python import PythonGrpcInterfaceGenerator
from util import create_truncated_string
from velocitas_lib import download_file, get_programming_language, get_project_cache_dir
from velocitas_lib.functional_interface import get_interfaces_for_type

DEPENDENCY_TYPE_KEY = "grpc-interface"


def download_proto(config: Dict[str, Any]) -> proto.ProtoFileHandle:
    """Download the proto file defined in the grpc-interface
    config to the local project cache.

    Args:
        config (Dict[str, Any]): The grpc-interface config.

    Returns:
        proto.ProtoFileHandle: A handle to the proto file.
    """
    service_if_spec_src = config["src"]
    _, filename = os.path.split(service_if_spec_src)

    cached_proto_file_path = os.path.join(get_project_cache_dir(), "services", filename)

    download_file(service_if_spec_src, cached_proto_file_path)

    return proto.ProtoFileHandle(cached_proto_file_path)


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
    generator: GrpcInterfaceGenerator, if_config: Dict[str, Any]
) -> None:
    """Generate an SDK for a single service.

    Args:
        generator (GrpcInterfaceGenerator):
            The generator to invoke for generating the SDK.
        if_config (Dict[str, Any]): The grpc-interface config.
    """
    print(
        f"Generating service SDK for {create_truncated_string(if_config['src'], 40)!r}"
    )
    proto_file_handle = download_proto(if_config)
    service_sdk_dir = create_service_sdk_dir(proto_file_handle)

    if "required" in if_config:
        generator.generate_service_client_sdk(service_sdk_dir, proto_file_handle)
    if "provided" in if_config:
        pass


def main(verbose: bool) -> None:
    """Generate service SDKs for all grpc-interfaces defined in the AppManifest.json.

    Args:
        verbose (bool): Enable verbose logging.
    """
    interfaces = get_interfaces_for_type(DEPENDENCY_TYPE_KEY)

    if len(interfaces) <= 0:
        return

    LANGUAGE_GENERATORS = {
        "cpp": CppGrpcInterfaceGenerator(verbose),
        "python": PythonGrpcInterfaceGenerator(verbose),
    }

    if get_programming_language() not in LANGUAGE_GENERATORS:
        print(
            "gRPC interface not yet supported for programming language "
            f"{get_programming_language()!r}"
        )
        return

    generator = LANGUAGE_GENERATORS[get_programming_language()]

    print("Installing tooling...")
    generator.install_tooling()

    for grpc_service in interfaces:
        if_config = grpc_service["config"]
        print("Generating service SDK...")
        generate_single_service(generator, if_config)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser("generate-sdk")
    argument_parser.add_argument("-v", "--verbose", action="store_true")
    args = argument_parser.parse_args()
    main(args.verbose)
