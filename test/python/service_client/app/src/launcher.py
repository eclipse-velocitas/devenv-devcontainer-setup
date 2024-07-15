# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

from typing import Optional

from hornservice_service_sdk.horn_pb2_grpc import HornServiceStub
from hornservice_service_sdk.HornServiceServiceClientFactory import (
    HornServiceServiceClientFactory,
)
from seats_service_sdk.seats_pb2_grpc import (
    SeatsStub,
)
from seats_service_sdk.SeatsServiceClientFactory import SeatsServiceClientFactory
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


def create_seats_client(middleware: Middleware) -> SeatsStub:
    client = SeatsServiceClientFactory.create(middleware)

    return client


def create_horn_client(middleware: Middleware) -> HornServiceStub:
    client = HornServiceServiceClientFactory.create(middleware)

    return client


SERVICE_ADRESS = "127.0.0.1:1234"

if __name__ == "__main__":
    middleware_client_mock = TestMiddleware(TestClientServiceLocator())

    create_seats_client(middleware_client_mock)
    create_horn_client(middleware_client_mock)
