# Copyright (c) 2023-2025 Contributors to the Eclipse Foundation
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

import os
import shutil
import subprocess
from typing import List

import pytest

if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "python":
    pytest.skip("skipping Python only tests", allow_module_level=True)


PACKAGE_NAME = "velocitas_sdk"


@pytest.fixture(autouse=True)
def clean_velocitas_download_directory():
    # return early if project directory does not yet exist
    if not os.path.isdir(
        os.path.join(os.path.expanduser("~"), ".velocitas", "projects")
    ):
        return

    shutil.rmtree(
        os.path.join(get_project_cache_dir(), "downloads"), ignore_errors=True
    )


@pytest.fixture(autouse=True)
def remove_preinstalled_package():
    remove_package(PACKAGE_NAME)


def get_subdirs(path: str) -> List[str]:
    return [f.path for f in os.scandir(path) if f.is_dir()]


def get_project_cache_dir() -> str:
    return subprocess.check_output(
        ["velocitas", "cache", "get", "--path"], encoding="utf-8"
    ).strip()


def is_package_installed(package_name: str) -> bool:
    return_code = subprocess.call(["pip", "show", package_name])
    return return_code == 0


def remove_package(package_name: str):
    subprocess.call(["pip", "uninstall", "-y", package_name])


def can_import_and_use_vehicleapp() -> bool:
    try:
        from velocitas_sdk.vehicle_app import VehicleApp

        class TestVehicleApp(VehicleApp):
            def __init__(self):
                pass

        app = TestVehicleApp()
        return app is not None
    except Exception as e:
        print("Exception:" + str(e))
        return False


def test_no_sdk_reference_found__nothing_installed():
    requirements_contents = """

    """
    with open(
        "./app/requirements-velocitas.txt", mode="w", encoding="utf-8"
    ) as requirements:
        requirements.write(requirements_contents)

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    assert not is_package_installed(PACKAGE_NAME) and not is_package_installed(
        PACKAGE_NAME.replace("_", "-")
    )


def test_sdk_reference_found__sdk_installed():
    requirements_contents = """
velocitas_sdk==0.13.0
    """
    with open(
        "./app/requirements-velocitas.txt", mode="w", encoding="utf-8"
    ) as requirements:
        requirements.write(requirements_contents)

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    assert is_package_installed(PACKAGE_NAME) or is_package_installed(
        PACKAGE_NAME.replace("_", "-")
    )
    assert can_import_and_use_vehicleapp()
