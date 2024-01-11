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
import subprocess


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """

    os.chdir(os.environ["VELOCITAS_TEST_ROOT"])

    # FIXME: The C++ base image does not install conan globally
    # but just for the vscode user, hence we have to download
    # conan manually here. Can be removed once conan is installed
    # globally.
    if os.environ["VELOCITAS_TEST_LANGUAGE"] == "cpp":
        subprocess.check_call(["python", "-m", "pip", "install", "conan==1.60.2"])

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
