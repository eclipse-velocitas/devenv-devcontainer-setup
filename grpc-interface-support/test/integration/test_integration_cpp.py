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


def get_dependency_count(service_name: str) -> int:
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

        if in_requires_section and line.strip() == f"{service_name}/generated":
            dependency_count = dependency_count + 1
    return dependency_count


def ensure_package_is_generated(service_name: str):
    service_path = os.path.join(get_project_cache_dir(), "services", service_name)

    assert os.path.isdir(service_path)
    assert os.path.isfile(os.path.join(service_path, "CMakeLists.txt"))
    assert os.path.isfile(os.path.join(service_path, "conanfile.py"))
    assert os.path.isdir(os.path.join(service_path, "include"))
    assert os.path.isdir(os.path.join(service_path, "src"))


def ensure_build_successful():
    assert subprocess.check_call(["velocitas", "exec", "build-system", "install"]) == 0
    assert subprocess.check_call(["velocitas", "exec", "build-system", "build"]) == 0


def ensure_app_running() -> subprocess.Popen:
    return subprocess.Popen(
        ["./build/bin/app"],
        env={
            "SDV_SEATS_ADDRESS": "127.0.0.1:1234",
            "SDV_VAL_ADDRESS": "127.0.0.1:1235",
            "SDV_HORNSERVICE_ADDRESS": "127.0.0.1:1236",
            "SDV_VCSPTCPBYLIMSERVICE_ADDRESS": "127.0.0.1:1237",
            "SDV_VCSMOTORTRQMNGSERVICE_ADDRESS": "127.0.0.1:1238",
        },
    )


def ensure_project_initialized():
    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0


def ensure_added_conan():
    assert get_dependency_count("seats-service-sdk") == 1
    assert get_dependency_count("hornservice-service-sdk") == 1
    assert get_dependency_count("val-service-sdk") == 1
    assert get_dependency_count("vcsptcpbylimservice-service-sdk") == 1
    assert get_dependency_count("vcsmotortrqmngservice-service-sdk") == 1


def ensure_packages_are_generated():
    ensure_package_is_generated("seats")
    ensure_package_is_generated("hornservice")
    ensure_package_is_generated("val")
    ensure_package_is_generated("vcsptcpbylimservice")
    ensure_package_is_generated("vcsmotortrqmngservice")


def test__integration():
    print("============= BUILDING SERVER ===================")
    os.chdir(os.environ["SERVICE_SERVER_ROOT"])
    ensure_project_initialized()
    ensure_packages_are_generated()
    ensure_added_conan()
    ensure_build_successful()
    server_process = ensure_app_running()

    print("============= BUILDING CLIENT ===================")
    os.chdir(os.environ["SERVICE_CLIENT_ROOT"])
    ensure_project_initialized()
    ensure_packages_are_generated()
    ensure_added_conan()
    ensure_build_successful()
    client_process = ensure_app_running()

    client_code = client_process.wait()
    server_process.kill()
    assert client_code == 0
