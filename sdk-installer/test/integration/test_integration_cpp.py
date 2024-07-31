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

PACKAGE_NAME = "vehicle-app-sdk"

if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "cpp":
    pytest.skip("skipping C++ only tests", allow_module_level=True)


@pytest.fixture(autouse=True)
def remove_preinstalled_package():
    print("Removing old packages")
    remove_package(PACKAGE_NAME)


def is_package_installed(package_name: str) -> bool:
    output = subprocess.check_output(
        ["conan", "search", package_name], encoding="utf-8"
    )
    return output.find("Existing package recipes:") != -1


def remove_package(package_name: str):
    subprocess.check_call(["conan", "remove", "-f", package_name])


def test_no_sdk_reference_found__nothing_installed():
    conanfile_contents = """
[requires]

    """
    with open("./conanfile.txt", mode="w", encoding="utf-8") as conanfile:
        conanfile.write(conanfile_contents)

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    assert not is_package_installed(PACKAGE_NAME)


def test_sdk_reference_found__sdk_installed():
    conanfile_contents = """
[requires]
vehicle-app-sdk/0.3.3
    """
    with open("./conanfile.txt", mode="w", encoding="utf-8") as conanfile:
        conanfile.write(conanfile_contents)

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    assert is_package_installed("vehicle-app-sdk")
