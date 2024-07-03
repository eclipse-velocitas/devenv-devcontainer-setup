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
from typing import Any, Dict, List, Optional

import proto
from cpp import CppGrpcServiceSdkGeneratorFactory
from generator import GrpcServiceSdkGeneratorFactory
from python import PythonGrpcServiceSdkGeneratorFactory
from velocitas_lib import (
    get_programming_language,
    get_project_cache_dir,
    get_workspace_dir,
    obtain_local_file_path,
)
from velocitas_lib.functional_interface import get_interfaces_for_type

DEPENDENCY_TYPE_KEY = "grpc-interface"
DOWNLOAD_PATH = os.path.join(get_project_cache_dir(), "downloads")


def extract_zip(file_path: str, extract_to: str) -> str:
    """Extract a zip file.

    Args:
        file_path (str): The file path to the zip.
        extract_to (str): The file path to extract to.

    Raises:
        RunTimeError if the file_path is not a zip.

    Returns:
        str: The file path to the extracted top level folder.
    """
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        return extract_to
    else:
        raise RuntimeError("Not a zip file!")


def discover_proto_files_in_filetree(
    tree_root: str, path_in_zip: Optional[str] = None
) -> List[proto.ProtoFileHandle]:
    """
    Recursively search for .proto files under the specified tree root.

    Args:
        tree_root (str): The path to the tree root to search from.
        path_in_zip (Optional[str]): The optional path_in_zip for zip directories.

    Returns:
        List[proto.ProtoFileHandle]: A list of file paths, relative to the search tree root, each pointing to a proto file.
    """
    proto_files = []
    if path_in_zip is not None:
        tree_root = os.path.join(tree_root, path_in_zip)
    for dir, _, files in os.walk(tree_root):
        for file in files:
            if file.endswith(".proto"):
                proto_files.append(proto.ProtoFileHandle(os.path.join(dir, file)))
    return proto_files


def check_zipfile(
    file_path: str, path_in_zip: Optional[str] = None
) -> List[proto.ProtoFileHandle]:
    """Check if the file is a .zip file and extracts it.

    Args:
        file_path (str): The path to a file.
        path_in_zip (Optional[str]): The optional path_in_zip for zip directories.

    Returns:
        List[proto.ProtoFileHandle]: A list of proto files.
    """

    if zipfile.is_zipfile(file_path):
        return discover_proto_files_in_filetree(
            extract_zip(file_path, DOWNLOAD_PATH),
            path_in_zip,
        )
    else:
        return [proto.ProtoFileHandle(file_path)]


def obtain_proto_files(
    path: str, path_in_zip: Optional[str] = None
) -> List[proto.ProtoFileHandle]:
    """Fetch the proto files defined in the grpc-interface
    config to the local project cache.

    Args:
        path (str): The path/uri to a file to download/an existing one or a directory containing proto files.
        path_in_zip (Optional[str]): directory to search for if path is zip

    Returns:
        List[proto.ProtoFileHandle]: A list of proto files.
    """
    if os.path.isdir(path):
        return discover_proto_files_in_filetree(path)
    elif os.path.isdir(os.path.join(get_workspace_dir(), path)):
        return discover_proto_files_in_filetree(os.path.join(get_workspace_dir(), path))
    else:
        path = obtain_local_file_path(path)
        return check_zipfile(path, path_in_zip)


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


def get_proto_include_dir(path: str) -> str:
    """Get the absolute path to the proto include directory.

    Args:
        path (str): The path to check.

    Raises:
        FileNotFoundError: In case the specified directory does not exist

    Returns:
        str: The absolute path to the proto include directory.
    """

    if os.path.isdir(path):
        return path
    elif os.path.isdir(os.path.join(get_workspace_dir(), path)):
        return os.path.join(get_workspace_dir(), path)
    if os.path.isdir(os.path.join(DOWNLOAD_PATH, path)):
        return os.path.join(DOWNLOAD_PATH, path)
    else:
        raise FileNotFoundError(f"Directory {path} not found!")


def generate_services(
    factory: GrpcServiceSdkGeneratorFactory, if_config: Dict[str, Any]
) -> None:
    """Generate SDKs for the services defined in the AppManifest..

    Args:
        factory (GrpcPackageGeneratorFactory):
            The factory from which to generate an SDK generator for a single service.
        if_config (Dict[str, Any]): The grpc-interface config.
    """

    path_in_zip = if_config.get("pathInZip", None)
    proto_file_handles = obtain_proto_files(if_config["src"], path_in_zip)
    is_client = "required" in if_config
    is_server = "provided" in if_config

    for proto_file in proto_file_handles:
        try:
            proto_include_dir = str(Path(proto_file.file_path).parent)
            if "protoIncludeDir" in if_config:
                proto_include_dir = get_proto_include_dir(if_config["protoIncludeDir"])
            generate_single_service(
                proto_file, factory, is_client, is_server, proto_include_dir
            )
        except RuntimeError:
            pass
            # skip a file with no service definition, can be an imported file


def generate_single_service(
    proto_file_handle: proto.ProtoFileHandle,
    factory: GrpcServiceSdkGeneratorFactory,
    generate_client: bool,
    generate_server: bool,
    proto_include_dir: str,
) -> None:
    """Generate an SDK for a single service.

    Args:
        proto_file_handle (proto:ProtoFileHandle): A file containing the service to generate.
        factory (GrpcPackageGeneratorFactory):
            The factory from which to generate an SDK generator for a single service.
        generate_client (bool):     Generates client code.
        generate_server (bool):     Generates server code.
        proto_include_dir (str):          The directory in which to search for imports.
    """

    service_sdk_dir = create_service_sdk_dir(proto_file_handle)
    print(f"Generating service SDK for {proto_file_handle.file_path}")

    generator = factory.create_service_generator(
        service_sdk_dir,
        proto_file_handle,
        proto_include_dir,
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
