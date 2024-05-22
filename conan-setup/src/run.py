# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

import json
import os
import subprocess
from typing import Dict, List, Optional

from velocitas_lib import get_workspace_dir
from velocitas_lib.variables import ProjectVariables


def conan_enable_revisions():
    subprocess.check_call(["conan", "config", "set", "general.revisions_enabled=1"])


def read_credentials_file() -> Dict[str, str]:
    credentials: Dict[str, str] = {}

    credentials_file_path = os.path.join(get_workspace_dir(), ".credentials")
    if not os.path.exists(credentials_file_path):
        raise FileNotFoundError("Missing .credentials file!")

    with open(credentials_file_path, encoding="utf-8") as file:
        for line in file.readlines():
            key = line[0 : line.index("=")].strip()
            value = line[line.index("=") + 1 :].strip()
            credentials[key] = value

    return credentials


def add_conan_remotes(remotes_array: List[Dict[str, str]]):
    vars_dict = os.environ
    vars_dict.update(read_credentials_file())
    project_variables = ProjectVariables(os.environ)

    for remote in remotes_array:
        conan_user = (
            project_variables.replace_occurrences(remote["user"])
            if "user" in remote
            else None
        )
        conan_token = (
            project_variables.replace_occurrences(remote["token"])
            if "token" in remote
            else None
        )
        conan_remote_id = remote["id"]
        conan_remote_url = remote["url"]
        setup_conan_remote(conan_remote_id, conan_remote_url, conan_token, conan_user)


def setup_conan_remote(
    remote_id: str,
    remote_url: str,
    remote_token: Optional[str],
    remote_user: Optional[str],
):
    """Sets up conan to use a new primary remote."""

    print(f"Adding conan remote: {remote_id!r}", end="")
    subprocess.check_call(
        ["conan", "remote", "add", "-f", remote_id, remote_url, "--insert", "0"]
    )

    if (
        remote_token is None
        or remote_id is None
        or len(remote_token) == 0
        or len(remote_id) == 0
    ):
        print(" with anonymous user")
        return

    subprocess.check_call(
        ["conan", "user", "-p", remote_token, "-r", remote_id, remote_user]
    )
    print(f" with user {remote_user!r}")


if __name__ == "__main__":
    additional_remotes_file_path = os.path.join(get_workspace_dir(), ".conanremotes")
    if os.path.exists(additional_remotes_file_path):
        additional_remotes = json.load(open(additional_remotes_file_path))

        conan_enable_revisions()
        add_conan_remotes(additional_remotes)
