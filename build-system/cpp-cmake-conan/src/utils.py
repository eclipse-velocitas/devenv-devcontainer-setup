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
from typing import List

from velocitas_lib import get_workspace_dir


def safe_get_workspace_dir() -> str:
    """A safe version of get_workspace_dir which defaults to '.'."""
    try:
        return get_workspace_dir().strip()
    except Exception:
        return os.path.abspath(".")


def get_build_folder(build_arch: str, host_arch: str):
    if host_arch == build_arch:
        return os.path.join(safe_get_workspace_dir(), "build")
    return os.path.join(safe_get_workspace_dir(), f"build_linux_{host_arch}")


def get_build_tools_path(build_folder_path: str) -> str:
    paths: List[str] = []
    with open(
        os.path.join(build_folder_path, "conanbuildinfo.txt"), encoding="utf-8"
    ) as file:
        for line in file:
            if line.startswith("PATH="):
                path_list = json.loads(line[len("PATH=") :])
                paths.extend(path_list)
    return ";".join(paths)


def load_toolchain(toolchain_file: str) -> None:
    if not os.path.exists(toolchain_file):
        raise FileNotFoundError(f"Toolchain file {toolchain_file} not found.")
    print(f"Loading toolchain file {toolchain_file}")

    proc = subprocess.Popen(
        ["env", "-i", "bash", "-c", f"source {toolchain_file} && env"],
        stdout=subprocess.PIPE,
    )
    if proc.stdout is not None:
        for line in proc.stdout:
            (key, _, value) = line.decode().partition("=")
            print(f"Setting {key} to {value}")
            os.environ[key] = value
    proc.communicate()
