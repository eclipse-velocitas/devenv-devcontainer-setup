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
import zipfile
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import proto
from cpp import CppGrpcServiceSdkGeneratorFactory
from generator import GrpcServiceSdkGeneratorFactory
from python import PythonGrpcServiceSdkGeneratorFactory
from velocitas_lib import (
    download_file,
    get_programming_language,
    get_project_cache_dir,
    obtain_local_file_path,
    get_workspace_dir
)
from velocitas_lib.functional_interface import get_interfaces_for_type
from velocitas_lib.text_utils import create_truncated_string

DEPENDENCY_TYPE_KEY = "grpc-interface"


def extract_zip(file_path: str, extract_to: str) -> str:
    """Extrcat a zip file.

    Args:
        file_path (str): The file path to the zip.
        extract_to (str): The fiel path to extract to.

    Returns:
        str: The file path to the extracted folder.
    """
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
        return extract_to


def find_proto_files(directory: str) -> List[proto.ProtoFileHandle]:
    """
    Recursively searches for .proto files under the specified directory.

    Args:
        directory (str): The path to the directory to search in.

    Returns:
        List[proto.ProtoFileHandle]: A list of proto files.
    """
    proto_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".proto"):
                proto_files.append(proto.ProtoFileHandle(os.path.join(root, file)))
    return proto_files


def fetch_protos(path: str) -> List[proto.ProtoFileHandle]:
    """Fetch the proto files defined in the grpc-interface
    config to the local project cache.

    Args:
        path (str): The path/uri to a file to download/an existing one or a directory containing proto files.

    Returns:
        List[proto.ProtoFileHandle]: A list of proto files.
    """
    if os.path.isfile(path):
        return [proto.ProtoFileHandle(path)]
    elif os.path.isfile(os.path.join(get_workspace_dir(), path)):
        return [proto.ProtoFileHandle(os.path.join(get_workspace_dir(), path))]
    elif os.path.isdir(path):
        return find_proto_files(path)
    elif os.path.isdir(os.path.join(get_workspace_dir(), path)):
        return find_proto_files(os.path.join(get_workspace_dir(), path))
    elif urlparse(path).scheme in ("http", "https"):
        _, filename = os.path.split(path)
        temp_dir = os.path.join(get_project_cache_dir(), "services")
        file_dir = os.path.join(temp_dir, filename)
        download_file(path, file_dir)
        if zipfile.is_zipfile(file_dir):
            return find_proto_files(extract_zip(file_dir, temp_dir))
        else:
            return [proto.ProtoFileHandle(filename)]
    else:
        raise ValueError("Path does not exist or is not a valid URL")


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


def generate_services(
    factory: GrpcServiceSdkGeneratorFactory, if_config: Dict[str, Any]
) -> None:
    """Generate an SDK for service(s).

    Args:
        factory (GrpcPackageGeneratorFactory):
            The factory from which to generate an SDK generator for a single service.
        if_config (Dict[str, Any]): The grpc-interface config.
    """

    proto_file_handles = fetch_protos(obtain_local_file_path(if_config["src"]))
    is_client = "required" in if_config
    is_server = "provided" in if_config

    for _proto in proto_file_handles:
        try:
            include_dir = if_config.get("includeDir", str(Path(proto.file_path).parent))
            generate_single_service(_proto, factory, is_client, is_server, include_dir)
        except RuntimeError:
            pass
            # skip a file with no service definition, can be an imported file


def generate_single_service(
    proto_file_handle: proto.ProtoFileHandle,
    factory: GrpcServiceSdkGeneratorFactory,
    generate_client: bool,
    generate_server: bool,
    include_dir: str,
) -> None:
    """Generate an SDK for a single service.

    Args:
        factory (GrpcPackageGeneratorFactory):
            The factory from which to generate an SDK generator for a single service.
        generate_client (bool):     Generates client code.
        generate_server (bool):     Generates server code.
        include_dir (str):          The directory in which to search for imports.
    """
    service_sdk_dir = create_service_sdk_dir(proto_file_handle)
    print(f"Generating service SDK for {proto_file_handle.file_path}")

    generator = factory.create_service_generator(
        service_sdk_dir,
        proto_file_handle,
        include_dir,
    )
    generator.generate_package(generate_client, generate_server)
    generator.install_package()
    generator.update_package_references()
    if generate_server:
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
        generate_services(factory, if_config)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("-v", "--verbose", action="store_true")
    args = argument_parser.parse_args()
    generate_sdks(args.verbose)
