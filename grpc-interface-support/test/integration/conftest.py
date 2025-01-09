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


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """

    client_path = "/tmp/service_client"
    server_path = "/tmp/service_server"

    shutil.copytree(os.environ["VELOCITAS_TEMPLATE_REPO_PATH"], client_path)
    shutil.copytree(os.environ["VELOCITAS_TEMPLATE_REPO_PATH"], server_path)

    shutil.copytree(
        f"{os.environ['VELOCITAS_PACKAGE_REPO_PATH']}/test/{os.environ['VELOCITAS_TEST_LANGUAGE']}/service_client",
        client_path,
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{os.environ['VELOCITAS_PACKAGE_REPO_PATH']}/test/{os.environ['VELOCITAS_TEST_LANGUAGE']}/service_server",
        server_path,
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{os.environ['VELOCITAS_PACKAGE_REPO_PATH']}/test/common/proto",
        server_path,
        dirs_exist_ok=True,
    )
    shutil.copytree(
        f"{os.environ['VELOCITAS_PACKAGE_REPO_PATH']}/test/common/proto",
        client_path,
        dirs_exist_ok=True,
    )
    shutil.copytree(
        "test/common/multiple/",
        server_path,
        dirs_exist_ok=True,
    )
    shutil.copytree(
        "test/common/multiple/",
        client_path,
        dirs_exist_ok=True,
    )

    os.environ["SERVICE_CLIENT_ROOT"] = client_path
    os.environ["SERVICE_SERVER_ROOT"] = server_path
