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
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from install_deps import install_model_generator  # noqa


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """

    # crude way of installing the model generator in the correct version
    # due to the version coming from the component manifest
    manifest_file_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "manifest.json"
    )
    manifest_dict = json.load(open(manifest_file_path))
    component_dict = manifest_dict["components"][1]
    os.environ["modelGeneratorGitRef"] = component_dict["variables"][2]["default"]
    os.environ["gitLocation"] = component_dict["variables"][3]["default"]
    install_model_generator()
