import io
import json
import os
import sys


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

    def __exit__(self, _type, _value, _traceback):
        del os.environ["VELOCITAS_CACHE_DIR"]
        del os.environ["VELOCITAS_WORKSPACE_DIR"]


def mock_env(app_manifest) -> MockEnv:
    return MockEnv(app_manifest)
