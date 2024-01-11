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
from pathlib import Path

import pytest
from test_lib import capture_stdout, mock_env

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from download_vspec import (  # noqa
    get_legacy_model_src,
    is_proper_interface_type,
    is_uri,
    main,
)

vspec_300_uri = "https://github.com/COVESA/vehicle_signal_specification/releases/download/v3.0/vss_rel_3.0.json"  # noqa


def get_vspec_file_path_value(capturedOutput: str) -> str:
    return (
        capturedOutput.split("vspec_file_path=")[1]
        .split(" >> VELOCITAS_CACHE")[0]
        .replace("'", "")
    )


def test_is_uri():
    assert is_uri(vspec_300_uri)
    assert is_uri("ftp://my-file")
    assert not is_uri("./local/path/to/file.file")


def test_get_legacy_model_src__camel_case_vehicle_model_key():
    app_manifest_dict = {"vehicleModel": {"src": "foo"}}
    assert get_legacy_model_src(app_manifest_dict) == "foo"


def test_get_legacy_model_src__pascal_case_vehicle_model_key():
    app_manifest_dict = {"VehicleModel": {"src": "bar"}}
    assert get_legacy_model_src(app_manifest_dict) == "bar"


def test_get_legacy_model_src__invalid_vehicle_model_key():
    app_manifest_dict = {"Vehicle.Model": {"src": "baz"}}
    with pytest.raises(KeyError):
        get_legacy_model_src(app_manifest_dict)


def test_proper_interface_type__wrong_type():
    assert not is_proper_interface_type({"type": "foo"})


def test_proper_interface_type__no_type():
    assert not is_proper_interface_type({"notype": "foo"})


def test_proper_interface_type__correct_type():
    assert is_proper_interface_type({"type": "vehicle-signal-interface"})


@pytest.mark.parametrize(
    "app_manifest",
    [
        {
            "manifestVersion": "v3",
            "interfaces": [
                {
                    "type": "vehicle-signal-interface",
                    "config": {"src": "./app/vspec.json"},
                }
            ],
        },
        {"VehicleModel": {"src": "./app/vspec.json"}},
    ],
)
def test_main__relative_src__converted_to_absolute(app_manifest):
    with capture_stdout() as capture, mock_env():
        main(app_manifest)

        vspec_file_path = get_vspec_file_path_value(capture.getvalue())
        assert os.path.isabs(vspec_file_path)
        assert vspec_file_path == "/workspaces/my_vehicle_app/app/vspec.json"


@pytest.mark.parametrize(
    "app_manifest",
    [
        {
            "manifestVersion": "v3",
            "interfaces": [
                {"type": "vehicle-signal-interface", "config": {"src": vspec_300_uri}}
            ],
        },
        {"VehicleModel": {"src": vspec_300_uri}},
    ],
)
def test_main__valid_app_manifest__uri_src_downloaded_and_stored_in_cache(app_manifest):
    with capture_stdout() as capture, mock_env():
        main(app_manifest)

        vspec_file_path = get_vspec_file_path_value(capture.getvalue())
        assert os.path.isabs(vspec_file_path)
        assert vspec_file_path == "/tmp/velocitas/vspec.json"


def test_main__duplicate_vehicle_signal_interface__raises_error():
    app_manifest = {
        "manifestVersion": "v3",
        "interfaces": [
            {"type": "vehicle-signal-interface", "config": {"src": vspec_300_uri}},
            {"type": "vehicle-signal-interface", "config": {"src": vspec_300_uri}},
        ],
    }
    with pytest.raises(KeyError):
        main(app_manifest)


def test_main__no_vehicle_signal_interface__adds_default_to_cache():
    app_manifest = {
        "manifestVersion": "v3",
        "interfaces": [{"type": "pubsub", "config": {}}],
    }
    with capture_stdout() as capture, mock_env():
        main(app_manifest)

        expected_path = str(
            Path(__file__).parent.parent.joinpath(
                "vehicle-model-lifecycle", "vspec.json"
            )
        )
        expected_cache_line = f"vspec_file_path={expected_path!r} >> VELOCITAS_CACHE\n"
        assert capture.getvalue() == expected_cache_line
