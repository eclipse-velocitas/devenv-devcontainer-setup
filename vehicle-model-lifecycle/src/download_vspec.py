# Copyright (c) 2023 Robert Bosch GmbH
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

"""Provides methods and functions to download vehicle model source files."""

import json
import os
import re

import requests


def require_env(name: str) -> str:
    """Require and return an environment variable.

    Args:
        name (str): The name of the variable.

    Raises:
        ValueError: In case the environment variable is not set.

    Returns:
        str: The value of the variable.
    """
    var = os.getenv(name)
    if not var:
        raise ValueError(f"environment variable {var!r} not set!")
    return var


def is_uri(path: str) -> bool:
    """Check if the provided path is a URI.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a URI. False otherwise.
    """
    return re.match(r"(\w+)\:\/\/(\w+)", path) is not None


def get_project_cache_dir() -> str:
    """Return the project's cache directory.

    Returns:
        str: The path to the project's cache directory.
    """
    return require_env("VELOCITAS_CACHE_DIR")


def get_velocitas_workspace_dir() -> str:
    """Return the project's workspace directory.

    Returns:
        str: The path to the project's workspace directory.
    """
    return require_env("VELOCITAS_WORKSPACE_DIR")


def download_file(uri: str, local_file_path: str):
    """Download vspec file from the given URI to the project cache.

    Args:
        uri (str): URI from which to download the file.
        local_file_path (str): The local path where to write file to
    """
    print(f"Downloading file from {uri!r} to {local_file_path!r}")
    with requests.get(uri) as infile:
        os.makedirs(os.path.split(local_file_path)[0], exist_ok=True)
        with open(local_file_path, "wb") as outfile:
            for chunk in infile.iter_content(chunk_size=8192):
                outfile.write(chunk)


def get_vehicle_model_src():
    manifest_data_str = require_env("VELOCITAS_APP_MANIFEST")
    manifest_data = json.loads(manifest_data_str)

    possible_keys = ["vehicle-model", "VehicleModel"]

    for key in possible_keys:
        if key in manifest_data:
            return manifest_data[key]["src"]

    raise KeyError("App manifest does not contain a valid vehicle model!")


def main():
    vspec_src = get_vehicle_model_src()
    local_vspec_path = os.path.join(
        get_velocitas_workspace_dir(), os.path.normpath(vspec_src)
    )

    if is_uri(vspec_src):
        local_vspec_path = os.path.join(get_project_cache_dir(), "vspec.json")
        download_file(vspec_src, local_vspec_path)

    vspec_src = local_vspec_path

    print(f"vspec_file_path={vspec_src!r} >> VELOCITAS_CACHE")


if __name__ == "__main__":
    main()
