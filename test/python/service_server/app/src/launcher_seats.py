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

import grpc
from seats_service_sdk.SeatsServiceServerFactory import SeatsServiceServerFactory
from SeatsServiceImpl import SeatsService
from test_middleware import TestMiddleware, TestServerServiceLocator
from velocitas_sdk.base import Middleware


def create_seats_server(middleware: Middleware) -> grpc.Server:
    servicer = SeatsService()

    return SeatsServiceServerFactory.create(
        middleware,
        servicer,
    )


if __name__ == "__main__":
    middleware_server_mock = TestMiddleware(TestServerServiceLocator())

    server = create_seats_server(middleware_server_mock)
    server.start()
    server.wait_for_termination()
