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
from typing import List, Optional

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
    project_caches = os.path.join(os.path.expanduser("~"), ".velocitas", "projects")
    return get_subdirs(project_caches)[0]


def test_python_package_is_generated():
    os.chdir(os.environ["SERVICE_CLIENT_ROOT"])
    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0

    assert_python_package_generated("seats")


def assert_python_package_generated(service_name: str):
    service_path = os.path.join(get_project_cache_dir(), "services", service_name)
    assert os.path.isdir(service_path)
    assert os.path.isfile(os.path.join(service_path, "pyproject.toml"))

    source_path = os.path.join(service_path, f"{service_name}_service_sdk")
    assert os.path.isdir(source_path)
    assert os.path.isfile(os.path.join(source_path, f"{service_name}_pb2_grpc.py"))
    assert os.path.isfile(os.path.join(source_path, f"{service_name}_pb2.py"))
    assert os.path.isfile(os.path.join(source_path, f"{service_name}_pb2.pyi"))


def test_pip_package_is_usable():
    from velocitas_sdk.base import Middleware, ServiceLocator

    class TestClientServiceLocator(ServiceLocator):
        def get_service_location(self, service_name: str) -> str:
            return f"{service_name}@127.0.0.1:1234"  # noqa: E231

        def get_metadata(self, service_name: Optional[str] = None):
            pass

    class TestServerServiceLocator(ServiceLocator):
        def get_service_location(self, service_name: str) -> str:
            return "127.0.0.1:1234"  # noqa: E231

        def get_metadata(self, service_name: Optional[str] = None):
            pass

    class TestMiddleware(Middleware):
        def __init__(self, serviceLocator: ServiceLocator) -> None:
            self.service_locator = serviceLocator

        async def start(self):
            pass

        async def wait_until_ready(self):
            pass

        async def stop(self):
            pass

    print("============= BUILDING SERVER ===================")
    os.chdir(os.environ["SERVICE_SERVER_ROOT"])
    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0

    from seats_service_sdk.seats_pb2_grpc import SeatsServicer
    from seats_service_sdk.SeatsServiceServerFactory import SeatsServiceServerFactory

    middleware = TestMiddleware(TestServerServiceLocator())
    servicer = SeatsServicer()

    server = SeatsServiceServerFactory.create(
        middleware,
        servicer,
    )

    assert server is not None

    print("============= BUILDING CLIENT ===================")
    os.chdir(os.environ["SERVICE_CLIENT_ROOT"])
    assert subprocess.check_call(["velocitas", "init", "-v"]) == 0

    from seats_service_sdk.SeatsServiceClientFactory import SeatsServiceClientFactory

    middleware = TestMiddleware(TestClientServiceLocator())
    client = SeatsServiceClientFactory.create(middleware)

    assert client is not None
