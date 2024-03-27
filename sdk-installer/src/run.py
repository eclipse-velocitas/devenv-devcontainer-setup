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
import json
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from velocitas_lib import (
    get_programming_language,
    get_project_cache_dir,
    get_workspace_dir,
    require_env,
)
from velocitas_lib.variables import ProjectVariables

SUPPORTED_LANGUAGES = ["cpp", "python"]


class PackageManager(ABC):
    @abstractmethod
    def is_package_installed(
        self, package_name: str, package_version: Optional[str] = None
    ) -> bool:
        ...

    @abstractmethod
    def get_required_package_version(self, package_name: str) -> Optional[str]:
        ...

    @abstractmethod
    def install_local_package(self, path: str) -> None:
        ...


class Conan(PackageManager):
    def __init__(self, verbose_logging: bool):
        self._verbose_logging = verbose_logging

    def is_package_installed(
        self, package_name: str, package_version: Optional[str] = None
    ) -> bool:
        search_pattern = package_name
        if package_version is not None:
            search_pattern = f"{package_name}@{package_version}"

        output = subprocess.check_output(
            ["conan", "search", search_pattern], encoding="utf-8"
        )
        return output.find("Existing package recipes:") != -1

    def get_required_package_version(self, package_name: str) -> Optional[str]:
        """Return the required version of the given package from the
        requirements file.

        Returns:
            str: The required version.
        """
        package_version: Optional[str] = None
        with open(
            os.path.join(get_workspace_dir(), "conanfile.txt"), encoding="utf-8"
        ) as conanfile:
            for line in conanfile:
                if line.startswith(f"{package_name}/"):
                    package_version = (
                        line.split("/", maxsplit=1)[1].split("@")[0].strip()
                    )

        return package_version

    def install_local_package(self, path: str) -> None:
        subprocess.check_call(
            ["conan", "export", "."],
            stdout=subprocess.DEVNULL if not self._verbose_logging else None,
            cwd=path,
        )



class Pip(PackageManager):
    def __init__(self, verbose_logging: bool):
        self._verbose_logging = verbose_logging

    def is_package_installed(
        self, package_name: str, package_version: Optional[str] = None
    ) -> bool:
        output = subprocess.check_output(
            ["pip", "list", package_name], encoding="utf-8"
        )

        package_found = False

        output_lines: List[str] = output.splitlines()
        for line in output_lines:
            package_data = line.strip().split(" ")
            if package_data[0].startswith(package_name):
                package_found = True
                if package_version is not None:
                    package_found = package_data[1] == package_version

        return package_found

    def get_required_package_version(self, package_name: str) -> Optional[str]:
        """Return the required version of the given package from the
        requirements file.

        Returns:
            str: The required version.
        """
        package_version: Optional[str] = None
        requirements_path = os.path.join(
            get_workspace_dir(), "app", "requirements-velocitas.txt"
        )
        if os.path.exists(requirements_path):
            with open(requirements_path, encoding="utf-8") as requirements_file:
                for line in requirements_file:
                    if line.replace("-", "_").startswith(
                        package_name.replace("-", "_")
                    ):
                        package_version = line.split("==")[1].strip()

        return package_version

    def install_local_package(self, path: str) -> None:
        subprocess.check_call(
            ["python", "-m", "pip", "install", "."],
            stdout=subprocess.DEVNULL if not self._verbose_logging else None,
            cwd=path,
        )


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


def get_package_manager(
    programming_language: str, verbose_logging: bool
) -> PackageManager:
    if programming_language == "cpp":
        return Conan(verbose_logging)
    elif programming_language == "python":
        return Pip(verbose_logging)

    raise RuntimeError(f"No package manager available for {programming_language!r}!")


def force_clone_repo(
    git_url: str, git_ref: str, output_dir: str, verbose_logging: bool
) -> None:
    """Clones the given git repository, forcefully removing any previously
    existing directory structure at the given output directory.

    Args:
        git_url (str): The URL of the git repo to clone.
        git_ref (str): The git ref (branch, tag, SHA) to clone.
        output_dir (str): The output directory to which to output the cloned
            repository.
        verbose_logging (bool): Enable verbose logging.
    """

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    subprocess.check_call(
        ["git", "clone", "--depth", "1", "-b", git_ref, git_url, output_dir],
        stdout=subprocess.DEVNULL if not verbose_logging else None,
    )

    subprocess.check_call(
        ["git", "config", "--global", "--add", "safe.directory", output_dir],
        stdout=subprocess.DEVNULL if not verbose_logging else None,
    )


def install_packge_if_required(
    package_dict: Dict[str, str], lang: str, verbose_logging: bool
):
    required_package_version: Optional[str] = None
    package_clone_path = os.path.join(
        get_project_cache_dir(), f"{package_dict['id']}-{lang}"
    )

    package_manager = get_package_manager(lang, verbose_logging)
    required_package_version = package_manager.get_required_package_version(
        package_dict["id"]
    )

    if required_package_version is None:
        print(
            f"No dependency on {package_dict['id']!r} detected -> Skipping installation."
        )
        return

    if package_manager.is_package_installed(
        package_dict["id"], required_package_version
    ):
        print(f"Correct version of {package_dict['id']!r} already installed!")
        return

    # clone git repository which contains SDK package
    git_url = package_dict["gitRepo"]
    project_variables = ProjectVariables(os.environ)
    git_url = project_variables.replace_occurrences(git_url)
    git_ref = package_dict["gitRef"]
    if git_ref == "auto":
        git_ref = get_tag_or_branch_name(required_package_version)

    force_clone_repo(git_url, git_ref, package_clone_path, verbose_logging)

    # install SDK
    print(
        f"Installing package version {required_package_version!r} from {git_url!r}..."
    )
    package_path = os.path.join(package_clone_path, package_dict["packageSubdirectory"])
    package_manager.install_local_package(package_path)


def main(verbose: bool):
    """Installs the SDKs of the supported languages.

    Args:
        verbose (bool): Enable verbose logging.
    """
    lang = get_programming_language()
    if lang not in SUPPORTED_LANGUAGES:
        print("No core SDK available yet for programming language " f"{lang!r}")
        return

    additional_packages = json.loads(require_env("additionalPackages"))
    for package in additional_packages:
        install_packge_if_required(package, lang, verbose)

    install_packge_if_required(
        {
            "id": "vehicle-app-sdk" if lang == "cpp" else "velocitas_sdk",
            "gitRepo": require_env("sdkGitRepo"),
            "gitRef": require_env("sdkGitRef"),
            "packageSubdirectory": require_env("sdkPackageSubdirectory"),
        },
        lang,
        verbose,
    )


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser("generate-sdk")
    argument_parser.add_argument("-v", "--verbose", action="store_true")
    args = argument_parser.parse_args()

    main(args.verbose)
