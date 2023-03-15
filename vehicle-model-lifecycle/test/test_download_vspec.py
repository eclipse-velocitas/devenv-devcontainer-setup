import io
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from download_vspec import download_file, is_uri, main  # noqa

vspec_300_uri = "https://github.com/COVESA/vehicle_signal_specification/releases/download/v3.0/vss_rel_3.0.json"  # noqa
app_manifest = {"VehicleModel": {"src": ""}}


def test_is_uri():
    assert is_uri(vspec_300_uri)
    assert is_uri("ftp://my-file")
    assert not is_uri("./local/path/to/file.file")


def test_download_file():
    local_file_path = "/tmp/mydownloadedfile"
    download_file(vspec_300_uri, local_file_path)

    assert os.path.isfile(local_file_path)


def test_vspec_file_path_from_absolute():
    capturedOutput = io.StringIO()
    sys.stdout = capturedOutput
    os.environ["VELOCITAS_CACHE_DIR"] = "/tmp/velocitas"
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "/workspaces/my_vehicle_app"

    app_manifest["VehicleModel"]["src"] = "./app/vspec.json"
    os.environ["VELOCITAS_APP_MANIFEST"] = json.dumps(app_manifest)

    main()
    sys.stdout = sys.__stdout__
    vspec_file_path = get_vspec_file_path_value(capturedOutput.getvalue())

    assert os.path.isabs(vspec_file_path)
    assert vspec_file_path == "/workspaces/my_vehicle_app/app/vspec.json"


def test_vspec_file_path_from_uri():
    capturedOutput = io.StringIO()
    sys.stdout = capturedOutput
    os.environ["VELOCITAS_CACHE_DIR"] = "/tmp/velocitas"
    os.environ["VELOCITAS_WORKSPACE_DIR"] = "/workspaces/my_vehicle_app"

    app_manifest["VehicleModel"]["src"] = vspec_300_uri
    os.environ["VELOCITAS_APP_MANIFEST"] = json.dumps(app_manifest)

    main()
    sys.stdout = sys.__stdout__
    vspec_file_path = get_vspec_file_path_value(capturedOutput.getvalue())

    assert os.path.isabs(vspec_file_path)
    assert vspec_file_path == "/tmp/velocitas/vspec.json"


def get_vspec_file_path_value(capturedOutput: str) -> str:
    return (
        capturedOutput.split("vspec_file_path=")[1]
        .split(" >> VELOCITAS_CACHE")[0]
        .replace("'", "")
    )
