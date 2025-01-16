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

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout


class ${{ service_name_camel_case }}ServiceConan(ConanFile):
    name = "${{ service_name_lower }}-service-sdk"
    version = "generated"

    # Optional metadata
    license = "Apache-2.0"
    author = "Eclipse Velocitas Contributors"
    url = "https://github.com/eclipse-velocitas/devenv-devcontainer-setup"
    description = "Auto-generated SDK for ${{ service_name_camel_case }}"
    topics = ("${{ service_name_camel_case }}", "gRPC", "RPC")

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    # Sources are located in the same place as this recipe, copy them to the recipe
    exports_sources = "CMakeLists.txt", "src/*", "include/*"

    # In general: Pin recipe revisions of dependencies having further dependencies to avoid build issues due to updated recipes
    # Workaround1: Pin recipe revision for transient dependency googleapis for enabling the container build
    # Workaround2: Pin recipe revision for transient dependency paho-mqtt-c cause latest is pulling libanl which cannot be found
    requires = [
        ("grpc/1.67.1"),
        ("protobuf/5.27.0"),
        ("vehicle-app-sdk/${{ core_sdk_version }}")
    ]

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["${{ service_name_lower }}-service-sdk"]
