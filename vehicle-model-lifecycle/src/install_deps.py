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

"""Provides methods and functions to download and install dependencies."""

import os
import subprocess
import sys


def require_env(name: str) -> str:
    """Require and return an environment variable.

    Args:
        name (str): The name of the variable.

    Raises:
        ValueError: In case the environment variable is not set.

    Returns:
        str: The value of the variable.
    """
    var = os.getenv(name)
    if not var:
        raise ValueError(f"environment variable {var!r} not set!")
    return var


def get_script_path() -> str:
    """Return the absolute path to the directory the invoked Python script
    is located in."""
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def pip(args: list[str]) -> None:
    """Invoke the pip process with the given arguments."""
    subprocess.check_call([sys.executable, "-m", "pip", *args])


def should_install_model_generator() -> bool:
    """Return whether to install the model generator or not."""
    env = os.getenv("installModelGenerator")

    if env is not None and env:
        return True

    return False


def install_packages() -> None:
    """Install all required Python packages for the model generator and
    VSpec download."""
    script_path = get_script_path()

    model_gen_repo = require_env("modelGeneratorGitRepo")
    model_gen_version = require_env("modelGeneratorGitRef")

    pip(["install", "-r", f"{script_path}/../requirements.txt"])

    if should_install_model_generator():
        pip(["install", f"git+{model_gen_repo}@{model_gen_version}"])


if __name__ == "__main__":
    install_packages()
