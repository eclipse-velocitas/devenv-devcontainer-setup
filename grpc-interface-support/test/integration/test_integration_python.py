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
import shutil
import subprocess
from typing import List

import pytest


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


if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "python":
    pytest.skip("skipping Python only tests", allow_module_level=True)


def get_subdirs(path: str) -> List[str]:
    return [f.path for f in os.scandir(path) if f.is_dir()]


def get_project_cache_dir() -> str:
    return subprocess.check_output(
        ["velocitas", "cache", "get", "--path"], encoding="utf-8"
    ).strip()


def start_app(python_file_name: str, env=os.environ) -> subprocess.Popen[bytes]:
    python_file = f"app/src/{python_file_name}.py"
    return subprocess.Popen(["python", python_file], env=env)


def assert_python_package_generated(service_name: str, proto_filename: str) -> None:
    service_path = os.path.join(get_project_cache_dir(), "services", service_name)
    assert os.path.isdir(service_path)
    assert os.path.isfile(os.path.join(service_path, "pyproject.toml"))

    source_path = os.path.join(service_path, f"{service_name}_service_sdk")
    assert os.path.isdir(source_path)
    assert os.path.isfile(os.path.join(source_path, f"{proto_filename}_pb2_grpc.py"))
    assert os.path.isfile(os.path.join(source_path, f"{proto_filename}_pb2.py"))
    assert os.path.isfile(os.path.join(source_path, f"{proto_filename}_pb2.pyi"))


def test_pip_package_is_generated():
    os.chdir(os.environ["SERVICE_CLIENT_ROOT"])
    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0

    assert_python_package_generated("seats", "seats")
    assert_python_package_generated("hornservice", "horn")


@pytest.mark.skip(
    "Skip b/c a running MQTT broker is required for the test at the moment. See: https://github.com/eclipse-velocitas/vehicle-app-python-sdk/issues/143"
)
def test_pip_package_is_usable():
    envs = os.environ.copy()
    envs["SDV_SEATS_ADDRESS"] = "127.0.0.1:1234"
    envs["SDV_HORNSERVICE_ADDRESS"] = "127.0.0.1:1235"

    print("============= TEST SERVER ===================")
    os.chdir(os.environ["SERVICE_SERVER_ROOT"])

    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0

    server_process = start_app("launcher", envs)

    print("============= TEST CLIENTS ===================")
    os.chdir(os.environ["SERVICE_CLIENT_ROOT"])

    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0

    client_process = start_app("launcher", envs)

    client_code = client_process.wait()
    server_process.kill()
    assert client_code == 0
