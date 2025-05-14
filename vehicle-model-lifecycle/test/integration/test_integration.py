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

import os
import shutil
import subprocess
from pathlib import Path


def copy_test_files() -> None:
    src = Path(__file__).parent.joinpath("data").joinpath("cpp_project")
    dst = "."
    shutil.copytree(src, dst, dirs_exist_ok=True)


def test_is_model_installed_cpp() -> None:
    if os.environ["VELOCITAS_TEST_LANGUAGE"] != "cpp":
        return

    output = subprocess.check_output(
        ["conan", "list", "vehicle-model"], encoding="utf-8"
    )

    assert output.find("ERROR") == -1


def test_package_can_be_used_by_project() -> None:
    if os.environ["VELOCITAS_TEST_LANGUAGE"] != "cpp":
        return

    copy_test_files()

    subprocess.check_call(["velocitas", "exec", "build-system", "install"])
    subprocess.check_call(["velocitas", "exec", "build-system", "build"])
