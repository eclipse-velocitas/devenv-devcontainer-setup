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

from val_service_sdk import VALServiceServerFactory
from VALServiceImpl import VALService
from vcsmotortrqmngservice_service_sdk import VCSMotorTrqMngServiceServiceServerFactory
from VCSMotorTrqMngServiceServiceImpl import VCSMotorTrqMngServiceService
from vcsptcpbylimservice_service_sdk import VCSPtCpbyLimServiceServiceServerFactory
from VCSPtCpbyLimServiceServiceImpl import VCSPtCpbyLimServiceService
from hornservice_service_sdk import HornServiceServiceServerFactory
from HornServiceServiceImpl import HornServiceService
from seats_service_sdk.SeatsServiceServerFactory import SeatsServiceServerFactory
from SeatsServiceImpl import SeatsService
from velocitas_sdk import config
from velocitas_sdk.base import Middleware


def start_seats_server(middleware: Middleware):
    servicer = SeatsService()

    server = SeatsServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()


def start_horn_server(middleware: Middleware):
    servicer = HornServiceService()

    server = HornServiceServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()


def start_val_server(middleware: Middleware):
    servicer = VALService()

    server = VALServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()


def start_motorcontrol_server(middleware: Middleware):
    servicer = VCSMotorTrqMngServiceService()

    server = VCSMotorTrqMngServiceServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()


def start_capacitycontrol_server(middleware: Middleware):
    servicer = VCSPtCpbyLimServiceService()

    server = VCSPtCpbyLimServiceServiceServerFactory.create(
        middleware,
        servicer,
    )
    server.start()


if __name__ == "__main__":
    start_horn_server(config.middleware)
    start_seats_server(config.middleware)
    start_val_server(config.middleware)
    start_motorcontrol_server(config.middleware)
    start_capacitycontrol_server(config.middleware)
