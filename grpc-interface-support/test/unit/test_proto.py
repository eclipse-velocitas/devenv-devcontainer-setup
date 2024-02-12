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

import os
import sys

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from proto import ProtoFileHandle  # noqa


proto_file_contents = """
package velocitas.toolchain.test.v1;

service TestService {
  rpc Method1(Method1Request) returns (Method1Response);
  rpc Method2(Method2Request) returns (Method2Response);
}
"""

proto_file_path = "/test.proto"


@pytest.fixture
def env():
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "/home/workspace"


@pytest.fixture
def mock_filesystem(fs: FakeFilesystem) -> FakeFilesystem:
    fs.create_file(proto_file_path, contents=proto_file_contents)
    return fs


def test_get_service_name(mock_filesystem: FakeFilesystem, env):
    proto_file = ProtoFileHandle(proto_file_path)
    assert proto_file.get_service_name() == "TestService"


def test_get_package(mock_filesystem: FakeFilesystem, env):
    proto_file = ProtoFileHandle(proto_file_path)
    assert proto_file.get_package() == "velocitas.toolchain.test.v1"
