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

import json
import os
import platform
import subprocess
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


def get_cli_version():
    velocitas_version_output = check_output(["velocitas", "--version"]).decode()
    search_velocitas_version_regex: Pattern[str] = compile(
        r"velocitas-cli\/(\w+.\w+.\w+).*"
    )
    cli_version = search(
        search_velocitas_version_regex, velocitas_version_output
    ).group(1)
    return f"v{cli_version}"


def test_post_start_auto_upgrade_cli():
    download_older_cli_version()
    # This should be the right check
    # But since we do not have a proper version output
    # on previous CLI releases we need to have a workaround
    # assert get_cli_version() == older_cli_version
    assert get_cli_version() == "v0.0.0"

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

    velocitas_json = open(".velocitas.json")
    data = json.load(velocitas_json)
    assert data["cliVersion"] == get_cli_version()


def test_files_synced():
    repo_path = os.environ["THIS_REPO_PATH"]
    print(repo_path)
    # check if there are any changes in the files to sync
    changed_files = (
        subprocess.check_output(
            ["git", "diff", "origin/main", "--name-only"],
            cwd=repo_path,
        )
        .decode()
        .split("\n")
    )
    language = os.environ["VELOCITAS_TEST_LANGUAGE"]

    changes_in_common = False
    changes_in_lang = False
    for changed_file in changed_files:
        changes_in_common = changes_in_common or (
            changed_file.find("setup/src/common") != -1
        )
        changes_in_lang = changes_in_lang or (
            changed_file.find(f"setup/src/{language}") != -1
        )

    subprocess.check_call(["velocitas", "init", "-f", "-v"], stdin=subprocess.PIPE)
    subprocess.check_call(["velocitas", "sync"])

    git_status_output = subprocess.check_output(
        ["git", "status", "--porcelain", "."]
    ).decode()

    if changes_in_common or changes_in_lang:
        assert git_status_output != ""
