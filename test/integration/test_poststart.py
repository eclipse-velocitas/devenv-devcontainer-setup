# Copyright (c) 2023 Robert Bosch GmbH
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
import platform
from re import Pattern, compile, search
from subprocess import PIPE, Popen, check_output

older_cli_version = "v0.5.4"


def get_cli_asset_name() -> str:
    platform_arch = platform.machine()
    cli_arch = "x64"
    if platform_arch == "aarch64":
        cli_arch = "arm64"
    return f"velocitas-linux-{cli_arch}"


def download_older_cli_version():
    cli_asset_name = get_cli_asset_name()
    cli_install_path = "/usr/bin/velocitas"
    cli_download_url = (
        "https://github.com/eclipse-velocitas/cli/"
        f"releases/download/{older_cli_version}/{cli_asset_name}"
    )

    print(
        f"Downloading CLI version {older_cli_version}"
        "from {cli_download_url} to {cli_install_path}"
    )
    download_cli = f"sudo curl -s -L {cli_download_url} -o {cli_install_path}"
    chmod = f"sudo chmod +x {cli_install_path}"

    cli_download_process = Popen(download_cli, stdout=PIPE, shell=True)
    cli_download_process.wait()
    Popen(chmod, stdout=PIPE, shell=True)


def test_post_start_auto_upgrade_cli():
    download_older_cli_version()

    post_create_script_path = os.path.join(
        os.getcwd(),
        ".devcontainer",
        "scripts",
        "postStartCommand.sh",
    )

    post_create_script_process = Popen(
        f"{post_create_script_path}", stdout=PIPE, shell=True
    )

    post_create_script_process.wait()

    velocitas_version_output = check_output(["velocitas", "--version"]).decode()
    search_velocitas_version_regex: Pattern[str] = compile(
        r"velocitas-cli\/(\w+.\w+.\w+).*"
    )
    updated_cli_version = search(
        search_velocitas_version_regex, velocitas_version_output
    ).group(1)

    velocitas_json = open(os.path.join(os.getcwd(), ".velocitas.json"))
    data = json.load(velocitas_json)
    assert data["cliVersion"] == f"v{updated_cli_version}"
