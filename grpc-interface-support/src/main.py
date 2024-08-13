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
from typing import Any, Dict

import proto
from cpp import CppGrpcServiceSdkGeneratorFactory
from generator import GrpcServiceSdkGeneratorFactory
from python import PythonGrpcServiceSdkGeneratorFactory
from velocitas_lib import (
    get_programming_language,
    get_project_cache_dir,
    get_workspace_dir,
    obtain_local_file_path,
    extract_zip,
    discover_files_in_filetree,
)
from velocitas_lib.functional_interface import get_interfaces_for_type

DEPENDENCY_TYPE_KEY = "grpc-interface"
DOWNLOAD_PATH = os.path.join(get_project_cache_dir(), "downloads")


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


def get_absolute_proto_include_path(relative_path: str) -> str:
    """Get the absolute path to the proto include directory.

    Args:
        relative_path (str): The relative path to check.

    Raises:
        FileNotFoundError: In case the specified directory does not exist

    Returns:
        str: The absolute path to the proto include directory.
    """

    if os.path.isabs(relative_path):
        return relative_path
    elif os.path.isdir(os.path.join(get_workspace_dir(), relative_path)):
        return os.path.join(get_workspace_dir(), relative_path)
    if os.path.isdir(os.path.join(DOWNLOAD_PATH, relative_path)):
        return os.path.join(DOWNLOAD_PATH, relative_path)
    else:
        raise FileNotFoundError(
            f"Directory {relative_path} not found! Searched additionally {get_workspace_dir()} and {DOWNLOAD_PATH}!"
        )


def generate_services(
    factory: GrpcServiceSdkGeneratorFactory, if_config: Dict[str, Any]
) -> None:
    """Generate SDKs for the services defined in the AppManifest.

    Raises:
        RuntimeError: If there is no service defined in any proto files given.

    Args:
        factory (GrpcPackageGeneratorFactory):
            The factory from which to generate an SDK generator for a single service.
        if_config (Dict[str, Any]): The grpc-interface config.
    """

    path_in_zip = if_config.get("pathInZip", None)
    path = if_config["src"]
    proto_files = []

    if os.path.isdir(path):
        pass
    elif os.path.isdir(os.path.join(get_workspace_dir(), path)):
        path = os.path.join(get_workspace_dir(), path)
    else:
        path = obtain_local_file_path(path)
        if zipfile.is_zipfile(path):
            path = extract_zip(path, DOWNLOAD_PATH)
            if path_in_zip is not None:
                path = os.path.join(path, path_in_zip)
        else:
            proto_files.append(path)

    proto_service_files = discover_files_in_filetree(path, ".proto")
    proto_files.extend(proto_service_files) if proto_service_files else None

    is_client = "required" in if_config
    is_server = "provided" in if_config
    skipped_files = 0

    for proto_file in proto_files:
        try:
            proto_service_file = proto.ProtoFileHandle(proto_file)
            proto_include_dir = str(Path(proto_service_file.file_path).parent)
            if "protoIncludeDir" in if_config:
                proto_include_dir = get_absolute_proto_include_path(
                    if_config["protoIncludeDir"]
                )
            generate_single_service(
                proto_service_file, factory, is_client, is_server, proto_include_dir
            )
        except RuntimeError:
            print(
                f"File {proto_file} has no services defined. If it is an import file ignore this error!"
            )
            skipped_files += 1

    if skipped_files == len(proto_files):
        raise RuntimeError("No services defined!")


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
        generate_client (bool):     Whether to create client code or not.
        generate_server (bool):     Whether to create server code or not.
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
