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
from velocitas_lib import get_workspace_dir

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from conan_helper import add_dependency_to_conanfile  # noqa


@pytest.fixture
def env():
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "/home/workspace"


def test_add_dependency_to_conanfile__only_requires_section(fs: FakeFilesystem, env):
    contents = """
[requires]
"""

    conanfile_path = os.path.join(get_workspace_dir(), "conanfile.txt")
    fs.create_file(conanfile_path, contents=contents)
    add_dependency_to_conanfile("mydep", "myver")

    expected = """
[requires]
mydep/myver
"""

    assert expected == open(conanfile_path, encoding="utf-8").read()


def test_add_dependency_to_conanfile__multiple_sections(fs: FakeFilesystem, env):
    contents = """
[requires]

[foo]

[bar]
"""

    conanfile_path = os.path.join(get_workspace_dir(), "conanfile.txt")
    fs.create_file(conanfile_path, contents=contents)
    add_dependency_to_conanfile("mydep", "myver")

    expected = """
[requires]
mydep/myver

[foo]

[bar]
"""

    assert expected == open(conanfile_path, encoding="utf-8").read()


def test_add_dependency_to_conanfile__no_requires_section(fs: FakeFilesystem, env):
    contents = """
[foo]

[bar]
"""

    conanfile_path = os.path.join(get_workspace_dir(), "conanfile.txt")
    fs.create_file(conanfile_path, contents=contents)
    add_dependency_to_conanfile("mydep", "myver")

    expected = """
[foo]

[bar]
[requires]
mydep/myver
"""

    assert expected == open(conanfile_path, encoding="utf-8").read()


def test_add_dependency_to_conanfile__pre_existing_dep_(fs: FakeFilesystem, env):
    contents = """
[foo]

[requires]
mydep/myver2

[bar]
"""

    conanfile_path = os.path.join(get_workspace_dir(), "conanfile.txt")
    fs.create_file(conanfile_path, contents=contents)
    add_dependency_to_conanfile("mydep", "myver")

    expected = """
[foo]

[requires]
mydep/myver

[bar]
"""

    assert expected == open(conanfile_path, encoding="utf-8").read()
