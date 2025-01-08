# Copyright (c) 2024-2025 Contributors to the Eclipse Foundation
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
import subprocess

import pytest

if not os.environ["VELOCITAS_TEST_LANGUAGE"] == "cpp":
    pytest.skip("skipping C++ only tests", allow_module_level=True)


def test_normal_build_successful():
    subprocess.check_call(
        ["velocitas", "exec", "build-system", "install"], stdin=subprocess.PIPE
    )
    subprocess.check_call(
        ["velocitas", "exec", "build-system", "build"], stdin=subprocess.PIPE
    )


def test_cross_build_successful():
    subprocess.check_call(
        ["sudo", "apt", "update"],
        stdin=subprocess.PIPE,
    )

    subprocess.check_call(
        [
            "sudo",
            "apt",
            "install",
            "-y",
            "gcc-aarch64-linux-gnu",
            "g++-aarch64-linux-gnu",
        ],
        stdin=subprocess.PIPE,
    )

    subprocess.check_call(
        ["velocitas", "exec", "build-system", "install", "-x", "aarch64"],
        stdin=subprocess.PIPE,
    )
    subprocess.check_call(
        ["velocitas", "exec", "build-system", "build", "-x", "aarch64"],
        stdin=subprocess.PIPE,
    )
