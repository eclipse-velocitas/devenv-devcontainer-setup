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

import glob
import os
import shutil
import subprocess
from typing import List, Optional, Tuple

from util import to_camel_case
from util.templates import CopySpec, copy_templates
from velocitas_lib import get_package_path, get_workspace_dir


def get_required_sdk_version() -> Optional[str]:
    """Return the required version of the core SDK.

    Returns:
        Optional[str]: The required version or None in case SDK is not a dependency.
    """
    sdk_version: Optional[str] = None
    with open(
        os.path.join(get_workspace_dir(), "conanfile.txt"), encoding="utf-8"
    ) as conanfile:
        for line in conanfile:
            if line.startswith("vehicle-app-sdk/"):
                sdk_version = line.split("/", maxsplit=1)[1].split("@")[0].strip()

    return sdk_version


def move_generated_sources(
    generated_source_dir: str, output_dir: str, include_dir_rel: str, src_dir_rel: str
) -> Tuple[List[str], List[str]]:
    """Move generated source code from the generation dir into
    headers: <output_dir>/<include_dir_rel>
    sources: <output_dir>/<src_dir_rel>

    Args:
        generated_source_dir (str): The directory containing the generated sources.
        output_dir (str): The root directory to move the generated files to.
        include_dir_rel (str): Path relative to output_dir where to move the headers to.
        src_dir_rel (str): Path relative to the output_dir where to move the sources to.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing
            [0] = a list of all headers
            [1] = a list of all sources
    """

    headers = glob.glob(os.path.join(generated_source_dir, "*.h"))
    sources = glob.glob(os.path.join(generated_source_dir, "*.cc"))

    headers_relative = []
    for header in headers:
        rel_path = os.path.relpath(header, generated_source_dir)
        os.makedirs(os.path.join(output_dir, include_dir_rel), exist_ok=True)
        shutil.move(header, os.path.join(output_dir, include_dir_rel, rel_path))
        headers_relative.append(os.path.join(include_dir_rel, rel_path))

    sources_relative = []
    for source in sources:
        rel_path = os.path.relpath(source, generated_source_dir)
        os.makedirs(os.path.join(output_dir, src_dir_rel), exist_ok=True)
        shutil.move(source, os.path.join(output_dir, src_dir_rel, rel_path))
        sources_relative.append(os.path.join(src_dir_rel, rel_path))

    return headers_relative, sources_relative


def create_conan_project(
    project_dir: str, interface_namespace: str, service_name: str
) -> None:
    """Create a conan project in the given project directory.

    Args:
        project_dir (str): The directory to create the project in.
        interface_namespace (str): The namespace of the proto file.
        service_name (str): The name of the service (from proto file).
    """

    include_dir = f"include/services/{service_name.lower()}"
    src_dir = f"src/services/{service_name.lower()}"

    headers_relative, sources_relative = move_generated_sources(
        project_dir, project_dir, include_dir, src_dir
    )

    files_to_copy = [
        CopySpec(source_path="CMakeLists.txt"),
        CopySpec(source_path="conanfile.py"),
        CopySpec(
            "ServiceNameServiceClientFactory.h",
            f"{include_dir}/{to_camel_case(service_name)}ServiceClientFactory.h",
        ),
        CopySpec(
            "ServiceNameServiceClientFactory.cc",
            f"{src_dir}/{to_camel_case(service_name)}ServiceClientFactory.cc",
        ),
    ]

    headers_relative.append(
        f"{include_dir}/{to_camel_case(service_name)}ServiceClientFactory.h"
    )
    sources_relative.append(
        f"{src_dir}/{to_camel_case(service_name)}ServiceClientFactory.cc"
    )

    variables = {
        "service_name": service_name,
        "service_name_lower": service_name.lower(),
        "service_name_camel_case": to_camel_case(service_name),
        "headers": "\n\t".join(headers_relative),
        "sources": "\n\t".join(sources_relative),
        "package_id": interface_namespace.replace(".", "::"),
        "core_sdk_version": str(get_required_sdk_version()),
    }

    template_dir = os.path.join(
        get_package_path(), "grpc-interface-support", "templates", "cpp"
    )

    copy_templates(template_dir, project_dir, files_to_copy, variables)


def export_conan_project(conan_project_path: str) -> None:
    """Export a conan project to the local conan cache.

    Args:
        conan_project_path (str): The path to directory containing the project.
    """
    print("Exporting Conan project")
    subprocess.check_call(
        ["conan", "export", "."],
        cwd=conan_project_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _find_insertion_index(
    lines: List[str], dependency_name: str
) -> Tuple[int, bool, bool]:
    """Find an insertion index for the dependency in a conanfile.txt.

    Args:
        lines (List[str]): The lines of the original conanfile.txt
        dependency_name (str): The name of the dependency (without version) e.g. "grpc"
            of the dependency to insert.

    Returns:
        Tuple[int, bool, bool]: A tuple consisting of
            [0] = Insert index.
            [1] = Whether the insert index replaces the original line or not.
            [2] = Whether the original file has a requires section or not.
    """
    found_index: Optional[int] = None
    replace: bool = False
    in_requires_section = False
    has_requires_section = False
    for i in range(0, len(lines)):
        stripped_line = lines[i].strip()
        if stripped_line == "[requires]":
            has_requires_section = True
            in_requires_section = True
            found_index = i + 1
        elif in_requires_section and stripped_line.startswith("["):
            in_requires_section = False

        if in_requires_section:
            if len(stripped_line) > 0:
                if stripped_line.startswith(dependency_name):
                    found_index = i
                    replace = True

    if found_index is None:
        found_index = len(lines)

    return (found_index, replace, has_requires_section)


def add_dependency_to_conanfile(dependency_name: str, dependency_version: str) -> None:
    """Add the dependency name to the project's list of dependencies.

    Args:
        dependency_name (str): The dependency to add e.g. grpc
        dependency_version (str): The version of the dependency to add e.g. 1.50.1
    """
    conanfile_path = os.path.join(get_workspace_dir(), "conanfile.txt")

    lines = []
    with open(conanfile_path, encoding="utf-8", mode="r") as conanfile:
        lines = conanfile.readlines()

    insert_index, replace, has_requires_section = _find_insertion_index(
        lines, dependency_name
    )

    dependency_line = f"{dependency_name}/{dependency_version}\n"
    if replace:
        lines[insert_index] = dependency_line
    else:
        if not has_requires_section:
            lines.insert(insert_index, "[requires]\n")
            insert_index = insert_index + 1
        lines.insert(insert_index, dependency_line)

    with open(conanfile_path, encoding="utf-8", mode="w") as conanfile:
        conanfile.writelines(lines)
