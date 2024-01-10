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

import io
import json
import os
import sys
from pathlib import Path


class StdoutCapturer:
    def __init__(self):
        self.capturedOutput = io.StringIO()

    def __enter__(self) -> io.StringIO:
        sys.stdout = self.capturedOutput
        return self.capturedOutput

    def __exit__(self, _type, _value, _traceback):
        sys.stdout = sys.__stdout__


def capture_stdout() -> StdoutCapturer:
    return StdoutCapturer()


class MockEnv:
    def __init__(
        self,
        app_manifest: dict[str, any],
        workspace_dir="/workspaces/my_vehicle_app",
        cache_dir="/tmp/velocitas",
    ):
        self.workspace_dir = workspace_dir
        self.cache_dir = cache_dir
        self.app_manifest = app_manifest

    def __enter__(self):
        os.environ["VELOCITAS_CACHE_DIR"] = self.cache_dir
        os.environ["VELOCITAS_WORKSPACE_DIR"] = self.workspace_dir
        os.environ["VELOCITAS_APP_MANIFEST"] = json.dumps(self.app_manifest)
        os.environ["VELOCITAS_PACKAGE_DIR"] = str(Path(__file__).parent.parent)

    def __exit__(self, _type, _value, _traceback):
        del os.environ["VELOCITAS_CACHE_DIR"]
        del os.environ["VELOCITAS_WORKSPACE_DIR"]


def mock_env(app_manifest=None) -> MockEnv:
    return MockEnv(app_manifest)
