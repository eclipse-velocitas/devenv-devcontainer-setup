import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
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
