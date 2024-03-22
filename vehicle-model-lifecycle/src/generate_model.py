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

"""Provides methods and functions to generate a vehicle model."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from shared_utils.conan_helper import add_dependency_to_conanfile, export_conan_project
from velocitas.model_generator import generate_model
from velocitas_lib import (
    get_cache_data,
    get_programming_language,
    get_project_cache_dir,
    get_workspace_dir,
    require_env,
)

CACHE_KEY = "vspec_file_path"
GENERATION_PATH_AUTO_DETECTION_KEY = "auto"


def get_model_output_dir() -> str:
    """Return the absolute path to the model output directory."""
    generation_path = os.path.join(get_project_cache_dir(), "vehicle_model")
    generation_path_override = require_env("generatedModelPath")
    if generation_path_override != GENERATION_PATH_AUTO_DETECTION_KEY:
        generation_path = generation_path_override

    if not generation_path.startswith("/"):
        generation_path = str(
            Path(os.path.join(get_workspace_dir(), generation_path)).resolve()
        )

    return generation_path


def remove_old_model(old_model_path: str) -> None:
    """Remove all traces of a previous vehicle model, if present."""
    print(f"Deleting old model at {old_model_path!r}")
    shutil.rmtree(old_model_path)


def invoke_generator(
    vspec_file_path: str, output_language: str, output_path: str
) -> None:
    """Invoke the model generator and produce a generated model in the cache
       directory.

    Args:
        vspec_file_path (str): The path to the vspec file.
        output_language (str): The programming language of the generated model.
        output_path (str): The path where the generated model is stored.
    """
    print(
        f"Invoking model generator for language {output_language} and file "
        f"{vspec_file_path!r}"
    )
    generate_model(vspec_file_path, output_language, output_path)


def install_model_if_required(language: str, model_path: str) -> None:
    """Install the model as package, if required by the language.

    Args:
        language (str): The output language of the model, i.e. python or cpp
        model_path (str): The path where the generated model is stored.
    """
    if language == "python":
        subprocess.check_call([sys.executable, "-m", "pip", "install", model_path])
    elif language == "cpp" and os.path.isfile(os.path.join(model_path, "conanfile.py")):
        export_conan_project(model_path)
    else:
        raise KeyError(f"{language!r} not supported!")


def add_model_dependency_if_required(language: str, model_path: str) -> None:
    if language == "cpp" and os.path.isfile(os.path.join(model_path, "conanfile.txt")):
        add_dependency_to_conanfile("vehicle-model", "generated")


def main() -> None:
    """Main entry point for generation of vehicle models."""
    cache_data = get_cache_data()

    if CACHE_KEY not in cache_data:
        return

    model_src_file = cache_data[CACHE_KEY]
    model_language = get_programming_language()
    model_output_dir = get_model_output_dir()

    os.makedirs(model_output_dir, exist_ok=True)

    remove_old_model(model_output_dir)
    invoke_generator(model_src_file, model_language, model_output_dir)
    install_model_if_required(model_language, model_output_dir)
    add_model_dependency_if_required(model_language, model_output_dir)


if __name__ == "__main__":
    main()
