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
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from generate_model import get_model_output_dir  # noqa


def test_get_model_output_dir_no_overwrite():
    os.environ["VELOCITAS_CACHE_DIR"] = "/tmp/velocitas"
    os.environ["generatedModelPath"] = "auto"
    output_dir = get_model_output_dir()

    assert output_dir == "/tmp/velocitas/vehicle_model"


def test_get_model_output_dir_with_overwrite():
    os.environ["VELOCITAS_CACHE_DIR"] = "/tmp/velocitas"
    os.environ["generatedModelPath"] = "/overwrite/path"
    output_dir = get_model_output_dir()

    assert output_dir == "/overwrite/path"


def test_get_model_output_dir_resolves_relative_path():
    os.environ["VELOCITAS_CACHE_DIR"] = "/tmp/velocitas"
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "/workspaces/my_vehicle_app"
    os.environ["generatedModelPath"] = "./gen/vehicle_model"
    output_dir = get_model_output_dir()

    assert output_dir == "/workspaces/my_vehicle_app/gen/vehicle_model"
