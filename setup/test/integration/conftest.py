import os
import subprocess


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """

    os.chdir(os.environ["VELOCITAS_TEST_ROOT"])

    # FIXME: The C++ base image does not install conan globally
    # but just for the vscode user, hence we have to download
    # conan manually here. Can be removed once conan is installed
    # globally.
    if os.environ["VELOCITAS_TEST_LANGUAGE"] == "cpp":
        subprocess.check_call(["python", "-m", "pip", "install", "conan==1.60.2"])
