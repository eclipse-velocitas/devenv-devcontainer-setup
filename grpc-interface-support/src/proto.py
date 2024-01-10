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


class ProtoFileHandle:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_package(self) -> str:
        """Return the package of the proto file.

        Raises:
            RuntimeError: In case there is no package ID in the proto file.

        Returns:
            str: The package of the proto file.
        """
        package_id = None
        with open(self.file_path, encoding="utf-8") as file:
            for line in file:
                if line.startswith("package"):
                    package_id = line.split(" ")[1][:-2]

        if package_id is None:
            raise RuntimeError("No package ID found in proto file!")

        return package_id

    def get_service_name(self) -> str:
        """Get the name of the service.

        Raises:
            RuntimeError: In case there is no defined service in the proto file.

        Returns:
            str: The name of the service.
        """
        service_name = None
        with open(self.file_path, encoding="utf-8") as file:
            for line in file:
                if line.startswith("service"):
                    service_name = line.split(" ")[1].strip()

        if service_name is None:
            raise RuntimeError("No service name found in proto file!")

        return service_name
