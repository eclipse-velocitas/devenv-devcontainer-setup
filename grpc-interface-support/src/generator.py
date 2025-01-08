# Copyright (c) 2023-2025 Contributors to the Eclipse Foundation
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


class GrpcServiceSdkGenerator(ABC):
    """Generator base class for service SDKs"""

    @abstractmethod
    def generate_package(self, client_required: bool, server_required: bool) -> None:
        """Generate the SDK package.

        Args:
            client_required (bool): Indicates whether a client factory shall be created.
            server_required (bool): Indicates whether a server factory shall be created.
        """
        pass

    @abstractmethod
    def install_package(self) -> None:
        """Install the generated package."""
        pass

    @abstractmethod
    def update_package_references(self) -> None:
        """Update all references to the generated package within the Velocitas workspace."""
        pass

    @abstractmethod
    def update_auto_generated_code(self) -> None:
        """Update auto-generated code within the Velocitas workspace."""
        pass


class GrpcServiceSdkGeneratorFactory(ABC):
    """Factory for creating service generators."""

    @abstractmethod
    def install_tooling(self) -> None:
        """Install required tooling for all created generators."""
        pass

    @abstractmethod
    def create_service_generator(
        self,
        output_path: str,
        proto_file_handle: proto.ProtoFileHandle,
        proto_include_path: str,
    ) -> GrpcServiceSdkGenerator:
        """Create a new service SDK generator for a specific service.

        Args:
            output_path (str): Path where the SDK shall be generated at.
            proto_file_handle (proto.ProtoFileHandle): The proto file which serves
                as the input for the generator.
            proto_include_path (str): The path which is used to look for imports.

        Returns:
            GrpcServiceSdkGenerator: A new GrpcServiceSdkGenerator which can
                generate a service SDK for the provided proto file.
        """
        pass
