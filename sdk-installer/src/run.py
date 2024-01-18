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

import argparse
import os
import re
import shutil
import subprocess
from typing import Optional

from velocitas_lib import (
    get_programming_language,
    get_project_cache_dir,
    get_workspace_dir,
)

SUPPORTED_LANGUAGES = ["cpp", "python"]


def get_required_sdk_version_cpp() -> str:
    """Return the required version of the C++ SDK.

    Returns:
        str: The required version.
    """
    sdk_version: str = "0.4.1"
    with open(
        os.path.join(get_workspace_dir(), "conanfile.txt"), encoding="utf-8"
    ) as conanfile:
        for line in conanfile:
            if line.startswith("vehicle-app-sdk/"):
                sdk_version = line.split("/", maxsplit=1)[1].split("@")[0].strip()

    return sdk_version


def get_required_sdk_version_python() -> str:
    """Return the required version of the Python SDK.

    Returns:
        str: The required version.
    """
    sdk_version: str = "0.12.0"
    requirements_path = os.path.join(
        get_workspace_dir(), "app", "requirements-velocitas.txt"
    )
    if os.path.exists(requirements_path):
        with open(requirements_path, encoding="utf-8") as requirements_file:
            for line in requirements_file:
                if line.startswith("velocitas-sdk"):
                    sdk_version = line.split("==")[1].strip()

    return sdk_version


def get_tag_or_branch_name(tag_or_branch_name: str) -> str:
    """Return the tag or branch name of a git ref.

    Args:
        tag_or_branch_name (str): A git ref.

    Returns:
        str: The version tag (prepended with a 'v' prefix)
            or the (unchanged) tag/branch name.
    """
    version_tag_pattern = re.compile(r"^[0-9]+(\.[0-9]+){0,2}$")
    if version_tag_pattern.match(tag_or_branch_name):
        return f"v{tag_or_branch_name}"
    return tag_or_branch_name


def main(verbose: bool):
    """Installs the SDKs of the supported languages.

    Args:
        verbose (bool): Enable verbose logging.
    """
    lang = get_programming_language()
    if lang not in SUPPORTED_LANGUAGES:
        print("gRPC interface not yet supported for programming language " f"{lang!r}")
        return

    required_sdk_version: Optional[str] = None
    sdk_install_path = os.path.join(get_project_cache_dir(), f"vehicle-app-{lang}-sdk")
    git_url = f"https://github.com/eclipse-velocitas/vehicle-app-{lang}-sdk.git"  # noqa: E231

    if lang == "cpp":
        required_sdk_version = get_required_sdk_version_cpp()
    elif lang == "python":
        required_sdk_version = get_required_sdk_version_python()

    if required_sdk_version is None:
        print("No SDK dependency detected -> Skipping installation.")
        return

    print(f"Installing version {required_sdk_version!r}...")

    if os.path.exists(sdk_install_path):
        shutil.rmtree(sdk_install_path)

    subprocess.check_call(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "-b",
            get_tag_or_branch_name(required_sdk_version),
            git_url,
        ],
        cwd=get_project_cache_dir(),
    )

    subprocess.check_call(
        ["git", "config", "--global", "--add", "safe.directory", sdk_install_path],
        stdout=subprocess.DEVNULL if not verbose else None,
    )

    if lang == "cpp":
        subprocess.check_call(
            ["conan", "export", "."],
            stdout=subprocess.DEVNULL if not verbose else None,
            cwd=sdk_install_path,
        )
    elif lang == "python":
        subprocess.check_call(
            ["python", "-m", "pip", "install", "."],
            stdout=subprocess.DEVNULL if not verbose else None,
            cwd=sdk_install_path,
        )


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser("generate-sdk")
    argument_parser.add_argument("-v", "--verbose", action="store_true")
    args = argument_parser.parse_args()
    main(args.verbose)
