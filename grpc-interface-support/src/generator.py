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

from abc import ABC, abstractmethod

import proto


class GrpcInterfaceGenerator(ABC):
    @abstractmethod
    def install_tooling(self) -> None:
        """Install required tooling for the generator."""
        pass

    @abstractmethod
    def generate_service_client_sdk(
        self, output_path: str, proto_file_handle: proto.ProtoFileHandle
    ) -> None:
        """Generate a service client for the given proto file.

        Args:
            output_path (str): The path at which to output the client SDK.
            proto_file_handle (proto.ProtoFileHandle): A proto file handle
                which represents the service contract.
        """
        pass

    @abstractmethod
    def generate_service_server_sdk(
        self, output_path: str, proto_file_handle: proto.ProtoFileHandle
    ) -> None:
        """Generate a service server for the given proto file.

        Args:
            output_path (str): The path at which to output the server SDK.
            proto_file_handle (proto.ProtoFileHandle): A proto file handle
                which represents the service contract.
        """
        pass
