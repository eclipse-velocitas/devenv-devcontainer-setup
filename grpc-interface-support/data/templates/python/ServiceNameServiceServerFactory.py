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
import concurrent.futures

from ${{ service_name_lower }}_service_sdk.${{ service_name_lower }}_pb2_grpc import (
    ${{ service_name }}Servicer, add_${{ service_name }}Servicer_to_server
)
from velocitas_sdk.base import Middleware

MAX_THREAD_POOL_WORKERS = 10

class ${{ service_name }}ServiceServerFactory:
    @staticmethod
    def create(middleware: Middleware, servicer: ${{ service_name }}Servicer) -> grpc.Server:
        address = middleware.service_locator.get_service_location("${{ service_name }}")
        server = grpc.server(concurrent.futures.ThreadPoolExecutor(MAX_THREAD_POOL_WORKERS))
        server.add_insecure_port(address)

        add_${{ service_name }}Servicer_to_server(servicer, server)

        return server
