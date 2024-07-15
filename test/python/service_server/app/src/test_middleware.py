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

from velocitas_sdk.base import Middleware, ServiceLocator

SERVICE_ADRESS = "127.0.0.1:1234"


class TestServerServiceLocator(ServiceLocator):
    def get_service_location(self, service_name: str) -> str:
        return SERVICE_ADRESS

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
