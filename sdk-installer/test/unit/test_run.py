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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from run import get_tag_or_branch_name  # noqa


def test_get_tag_or_branch_name__semver_input__returns_valid_tag():
    assert "v0.1.0" == get_tag_or_branch_name("0.1.0")
    assert "v2.0" == get_tag_or_branch_name("2.0")
    assert "v3" == get_tag_or_branch_name("3")


def test_get_tag_or_branch_name__branch_name_input__returns_branch_name():
    assert "foo" == get_tag_or_branch_name("foo")
    assert "1bar" == get_tag_or_branch_name("1bar")
    assert "baz2" == get_tag_or_branch_name("baz2")
