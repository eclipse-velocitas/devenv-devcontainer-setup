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


from hornservice_service_sdk.horn_pb2 import IsRunningRequest
from hornservice_service_sdk.horn_pb2_grpc import HornServiceStub
from hornservice_service_sdk.HornServiceServiceClientFactory import (
    HornServiceServiceClientFactory,
)
from seats_service_sdk.seats_pb2_grpc import (
    SeatsStub,
)
from seats_service_sdk.seats_pb2 import MoveRequest
from seats_service_sdk.SeatsServiceClientFactory import SeatsServiceClientFactory
from velocitas_sdk.base import Middleware
from velocitas_sdk import config


def create_seats_client(middleware: Middleware) -> SeatsStub:
    client = SeatsServiceClientFactory.create(middleware)

    return client


def create_horn_client(middleware: Middleware) -> HornServiceStub:
    client = HornServiceServiceClientFactory.create(middleware)

    return client


if __name__ == "__main__":
    client_seats = create_seats_client(config.middleware)
    move_request = MoveRequest()
    client_seats.Move(move_request)

    client_horn = create_horn_client(config.middleware)
    is_running_request = IsRunningRequest()
    client_horn.IsRunning(is_running_request)
