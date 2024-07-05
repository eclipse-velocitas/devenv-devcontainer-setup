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

from typing import List

from proto_schema_parser import ast
from proto_schema_parser.parser import Parser


class ProtoFileHandle:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.service_name = self.get_service_name()
        self.imports = self.get_imports()

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
        with open(self.file_path, "r") as file:
            parsed_data = Parser().parse(file.read())

        for element in parsed_data.file_elements:
            if isinstance(element, ast.Service):
                service_name = str(element.name)

        if service_name is None:
            raise RuntimeError("No service name found in proto file!")

        return service_name

    def get_imports(self) -> List[str]:
        """Get the name of the imports.

        Returns:
            List[str]: The names to the imports
        """
        imports = []
        with open(self.file_path, "r") as file:
            parsed_data = Parser().parse(file.read())

        for element in parsed_data.file_elements:
            if isinstance(element, ast.Import):
                imports.append(str(element.name))

        return imports
