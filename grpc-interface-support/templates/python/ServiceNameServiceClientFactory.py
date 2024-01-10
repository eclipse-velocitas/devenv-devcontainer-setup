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

import grpc
from ${{ service_name_lower }}_service_sdk.${{ service_name_lower }}_pb2_grpc import (
    ${{ service_name }}Stub,
)
from velocitas_sdk.base import Middleware


class ${{ service_name_camel_case }}ServiceClientFactory:
    @staticmethod
    def create(middleware: Middleware) -> ${{ service_name }}Stub:
        address = middleware.service_locator.get_service_location("${{ service_name }}")
        channel = grpc.aio.insecure_channel(address)

        return ${{ service_name }}Stub(channel)
