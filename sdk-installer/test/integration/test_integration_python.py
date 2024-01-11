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

import os
import subprocess

import pytest

if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "python":
    pytest.skip("skipping Python only tests", allow_module_level=True)


def is_package_installed(package_name: str) -> bool:
    output = subprocess.check_output(["pip", "show", package_name], encoding="utf-8")
    return output.find(f"Name: {package_name}") != -1


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


def test_no_sdk_reference_found__latest_version_installed():
    requirements_contents = """

    """
    with open("./app/requirements-velocitas.txt", mode="w") as conanfile:
        conanfile.write(requirements_contents)

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    assert is_package_installed("velocitas-sdk")
    assert can_import_and_use_vehicleapp()


def test_sdk_reference_found__sdk_installed():
    requirements_contents = """
velocitas-sdk==0.12.0
    """
    with open("./app/requirements-velocitas.txt", mode="w") as conanfile:
        conanfile.write(requirements_contents)

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    assert is_package_installed("velocitas-sdk")
    assert can_import_and_use_vehicleapp()
