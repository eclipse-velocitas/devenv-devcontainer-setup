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
from typing import Dict, List, Optional


class CopySpec:
    """Copy specification of a single file or directory."""

    def __init__(self, source_path: str, target_path: Optional[str] = None):
        self.source_path = source_path
        self.target_path = target_path

    def get_target(self) -> str:
        """Get the target path of the copy spec.

        Returns:
            str: If a target_path is given explicitly, it will be returned.
                 Otherwise the source_path will be returned.
        """
        if self.target_path is not None:
            return self.target_path
        return self.source_path


def copy_templates(
    template_dir: str,
    target_dir: str,
    template_file_mapping: List[CopySpec],
    variables: Dict[str, str],
) -> None:
    """Copy templates from the template dir to the target dir.

    Args:
        template_dir (str): Path to the directory containing the template files.
        target_dir (str): Path to the target directory.
        template_file_mapping (Dict[str, str]): A mapping of source path to target path.
        variables (Dict[str, str]): Name to value mapping which will be replaced when parsing the template files.
    """
    for file_to_copy in template_file_mapping:
        with open(
            os.path.join(
                template_dir,
                file_to_copy.source_path,
            ),
            encoding="utf-8",
        ) as file_in:
            target_file_path = os.path.join(target_dir, file_to_copy.get_target())

            os.makedirs(os.path.split(target_file_path)[0], exist_ok=True)
            with open(target_file_path, encoding="utf-8", mode="w") as file_out:
                lines = file_in.readlines()
                for line in lines:
                    for key, value in variables.items():
                        line = line.replace("${{ " + key + " }}", value)
                    file_out.write(line)
