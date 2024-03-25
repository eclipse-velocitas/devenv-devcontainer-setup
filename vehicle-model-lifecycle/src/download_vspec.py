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

"""Provides methods and functions to download vehicle model source files."""

import os
import re
from typing import Any, Dict, List, Tuple

from velocitas_lib import (
    download_file,
    get_app_manifest,
    get_project_cache_dir,
    get_workspace_dir,
    require_env,
)

FUNCTIONAL_INTERFACE_TYPE_KEY = "vehicle-signal-interface"


def is_uri(path: str) -> bool:
    """Check if the provided path is a URI.

    Args:
        path (str): The path to check.

    Returns:
        bool: True if the path is a URI. False otherwise.
    """
    return re.match(r"(\w+)\:\/\/(\w+)", path) is not None


def is_legacy_app_manifest(app_manifest_dict: Dict[str, Any]) -> bool:
    """Check if the used app manifest is a legacy file.

    Args:
        app_manifest_dict (Dict[str, Any]): The app manifest.

    Returns:
        bool: True if the app manifest is a legacy file, False if not.
    """
    return "manifestVersion" not in app_manifest_dict


def get_legacy_model_src(app_manifest_dict: Dict[str, Any]) -> str:
    """Get the source from the legacy vehicle model (app manifest < v3)

    Args:
        app_manifest_dict (Dict[str, Any]): The app manifest dict.

    Returns:
        str: The source URI of the vehicle model
    """
    possible_keys = ["vehicleModel", "VehicleModel"]

    for key in possible_keys:
        if key in app_manifest_dict:
            return str(app_manifest_dict[key]["src"])

    raise KeyError("App manifest does not contain a valid vehicle model!")


def is_proper_interface_type(interface: Dict[str, Any]) -> bool:
    """Return if the interface is of the correct type.

    Args:
        interface (Dict[str, Any]): The interface to check.

    Returns:
        bool: True if the type matches, False otherwise.
    """
    return "type" in interface and interface["type"] == FUNCTIONAL_INTERFACE_TYPE_KEY


def get_vehicle_signal_interfaces(
    app_manifest_dict: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Return all vehicle signal interfaces in the app manifest.

    Args:
        app_manifest_dict (Dict[str, Any]): The app manifest.

    Returns:
        List[Dict[str, Any]]: List containing all functional interfaces
            of type {FUNCTIONAL_INTERFACE_TYPE_KEY}
    """
    interfaces = list()

    for interface in app_manifest_dict["interfaces"]:
        if is_proper_interface_type(interface):
            interfaces.append(interface)

    return interfaces


def get_vehicle_signal_interface_src(
    interface: Dict[str, Any],
) -> Tuple[str, List[str]]:
    """Return the URI of the source for the Vehicle Signal Interface and the matching unit file(s).

    Args:
        interface (Dict[str, Any]): The interface.

    Returns:
        Tuple[str, List[str]]: The URI of the source for the Vehicle Signal Interface and a list of the matching unit file(s)
    """
    if "config" in interface:
        if "src" in interface["config"]:
            src = str(interface["config"]["src"])
        else:
            src = require_env("vssSrc")

        if "unit_src" in interface["config"]:
            unit_src_list = interface["config"]["unit_src"]
            if not isinstance(unit_src_list, list) or not all(
                isinstance(item, str) for item in unit_src_list
            ):
                raise Exception("No list of strings specified, please do ['src1', ...]")
        else:
            unit_src_list = [require_env("vssUnitSrc")]
    else:
        src = require_env("vssSrc")
        unit_src_list = [require_env("vssUnitSrc")]

    return src, unit_src_list


def get_vehicle_signal_interface_unit_files(unit_src_list: List[str]) -> List[str]:
    """Return a list of paths to unit files.

    Args:
        unit_src_list List[str]: List with uri's or a mixture of local paths and uri's.

    Returns:
        List[str]]: List with local paths to the unit file(s).
    """
    id = 0
    list = []
    for unit_src in unit_src_list:
        if is_uri(unit_src):
            local_unit_path = os.path.join(get_project_cache_dir(), f"units_{id}.yaml")
            # since there is no release for units file 4.0 we need to download from blob and this is different than downloading from release
            print(f"Downloading file from {unit_src!r} to {local_unit_path!r}")
            download_file(unit_src, local_unit_path)
            list.append(local_unit_path)
            id += 1
        else:
            list.append(unit_src)

    return list


def main(app_manifest_dict: Dict[str, Any]) -> None:
    """Entry point for downloading the vspec file for a
    vehicle-signal-interface.

    Args:
        app_manifest_dict (Dict[str, Any]): The app manifest.

    Raises:
        KeyError: If there are multiple vehicle signal interfaces defined
            in the app manifest.
    """
    if is_legacy_app_manifest(app_manifest_dict):
        vspec_src = get_legacy_model_src(app_manifest_dict)
        unit_src_list = [require_env("vssUnitSrc")]
    else:
        interfaces = get_vehicle_signal_interfaces(app_manifest_dict)
        if len(interfaces) > 1:
            raise KeyError(
                f"Only up to one {FUNCTIONAL_INTERFACE_TYPE_KEY!r} supported!"
            )
        elif len(interfaces) == 1:
            vspec_src, unit_src_list = get_vehicle_signal_interface_src(interfaces[0])
        else:
            # FIXME: Fallback solution in case an app does not provide a VSS
            #        file. Code path can be removed once we have a dependency
            #        resolver for our runtimes.
            vspec_src = require_env("vssSrc")
            unit_src_list = [require_env("vssUnitSrc")]

    local_vspec_path = os.path.join(get_workspace_dir(), os.path.normpath(vspec_src))

    if is_uri(vspec_src):
        local_vspec_path = os.path.join(get_project_cache_dir(), "vspec.json")
        print(f"Downloading file from {vspec_src!r} to {local_vspec_path!r}")
        download_file(vspec_src, local_vspec_path)

    unit_src_list = get_vehicle_signal_interface_unit_files(unit_src_list)

    vspec_src = local_vspec_path
    if list:
        unit_src_list = list
    print(f"vspec_file_path={vspec_src!r} >> VELOCITAS_CACHE")
    print(f"unit_file_path_list={unit_src_list!r} >> VELOCITAS_CACHE")


if __name__ == "__main__":
    main(get_app_manifest())
