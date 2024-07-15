# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
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

"""A sample skeleton vehicle app."""

from hornservice_service_sdk.HornServiceServiceServerFactory import (
    HornServiceServiceServerFactory,
)
from HornServiceServiceImpl import HornServiceService
from seats_service_sdk.SeatsServiceServerFactory import SeatsServiceServerFactory
from SeatsServiceImpl import SeatsService
from velocitas_sdk import config
from velocitas_sdk.base import Middleware


def create_seats_server(middleware: Middleware):
    servicer = SeatsService()

    server = SeatsServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()
    server.wait_for_termination()


def create_horn_server(middleware: Middleware):
    servicer = HornServiceService()

    server = HornServiceServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    create_horn_server(config.middleware)
    create_seats_server(config.middleware)
