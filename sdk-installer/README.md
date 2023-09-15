# SDK Installer

This component installs the Velocitas core SDK if it is referenced by the Vehicle Applications requirements file.

## About

At the moment, both core SDKs are not available through central package repositories (PyPI, Conan Center). Therefore, to use the core SDKs, they need to be made available to the package managers through other means. This is where this component comes in. It finds the required version from either `app/requirements.txt` or `conanfile.txt`, clones the respective SDK's git repository and exports the package to the local package registry.
