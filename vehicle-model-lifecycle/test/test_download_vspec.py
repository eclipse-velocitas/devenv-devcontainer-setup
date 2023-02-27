import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from download_vspec import download_file, is_uri  # noqa

vspec_300_uri = "https://github.com/COVESA/vehicle_signal_specification/releases/download/v3.0/vss_rel_3.0.json"  # noqa


def test_is_uri():
    assert is_uri(vspec_300_uri)
    assert is_uri("ftp://my-file")
    assert not is_uri("./local/path/to/file.file")


def test_download_file():
    local_file_path = "/tmp/mydownloadedfile"
    download_file(vspec_300_uri, local_file_path)

    assert os.path.isfile(local_file_path)
