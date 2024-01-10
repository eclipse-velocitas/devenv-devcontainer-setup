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
from typing import List, Optional

import pytest

if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "python":
    pytest.skip("skipping Python only tests", allow_module_level=True)


def get_subdirs(path: str) -> List[str]:
    return [f.path for f in os.scandir(path) if f.is_dir()]


def get_project_cache_dir() -> str:
    project_caches = os.path.join(os.path.expanduser("~"), ".velocitas", "projects")
    return get_subdirs(project_caches)[0]


def test_python_package_is_generated():
    service_path = os.path.join(get_project_cache_dir(), "services", "seats")
    assert os.path.isdir(service_path)
    assert os.path.isfile(os.path.join(service_path, "pyproject.toml"))

    source_path = os.path.join(service_path, "seats_service_sdk")
    assert os.path.isdir(source_path)
    assert os.path.isfile(os.path.join(source_path, "seats_pb2_grpc.py"))
    assert os.path.isfile(os.path.join(source_path, "seats_pb2.py"))
    assert os.path.isfile(os.path.join(source_path, "seats_pb2.pyi"))


def test_pip_package_is_usable():
    from seats_service_sdk.SeatsServiceClientFactory import SeatsServiceClientFactory
    from velocitas_sdk.base import Middleware, ServiceLocator

    class TestServiceLocator(ServiceLocator):
        def get_service_location(self, service_name: str) -> str:
            return f"{service_name}@anyserver:anyport"  # noqa: E231

        def get_metadata(self, service_name: Optional[str] = None):
            pass

    class TestMiddleware(Middleware):
        def __init__(self) -> None:
            self.service_locator = TestServiceLocator()

        async def start(self):
            pass

        async def wait_until_ready(self):
            pass

        async def stop(self):
            pass

    middleware = TestMiddleware()
    client = SeatsServiceClientFactory.create(middleware)

    assert client is not None
