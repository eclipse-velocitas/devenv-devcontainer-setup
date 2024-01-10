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
from typing import List

import pytest

if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "cpp":
    pytest.skip("skipping C++ only tests", allow_module_level=True)


def get_subdirs(path: str) -> List[str]:
    return [f.path for f in os.scandir(path) if f.is_dir()]


def get_project_cache_dir() -> str:
    project_caches = os.path.join(os.path.expanduser("~"), ".velocitas", "projects")
    return get_subdirs(project_caches)[0]


def test_grpc_package_is_generated():
    service_path = os.path.join(get_project_cache_dir(), "services", "seats")

    assert os.path.isdir(service_path)
    assert os.path.isfile(os.path.join(service_path, "CMakeLists.txt"))
    assert os.path.isfile(os.path.join(service_path, "conanfile.py"))
    assert os.path.isdir(os.path.join(service_path, "include"))
    assert os.path.isdir(os.path.join(service_path, "src"))


def test_project_depends_on_grpc_package():
    # Use a number rather than a bool to ensure
    # the generator has added the dependency only
    # once.
    dependency_count = 0
    in_requires_section = False
    for line in open("./conanfile.txt"):
        if line.strip() == "[requires]":
            in_requires_section = True
        elif line.startswith("["):
            in_requires_section = False

        if in_requires_section and line.strip() == "seats-service-sdk/generated":
            dependency_count = dependency_count + 1

    assert dependency_count == 1


def test_project_is_buildable():
    assert subprocess.check_call(["./install_dependencies.sh"]) == 0
    assert subprocess.check_call(["./build.sh"]) == 0
