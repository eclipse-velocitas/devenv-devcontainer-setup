#!/bin/bash
# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
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

# exit when any command fails
set -e

# restart Docker connection if in Codespaces
# Workaround according to https://github.com/devcontainers/features/issues/671#issuecomment-1701754897
if [ "${CODESPACES}" = "true" ]; then
    sudo pkill dockerd && sudo pkill containerd
    /usr/local/share/docker-init.sh
fi

echo "#######################################################"
echo "### Run VADF Lifecycle Management                   ###"
echo "#######################################################"

 # Line below intended for automatic addition of additional pip configurations
 # Do not change or remove
 # PIP_EXTRA_CONFIG

if [ -z "${VELOCITAS_OFFLINE}" ]; then
    .devcontainer/scripts/upgrade-cli.sh
fi

velocitas init
velocitas sync

sudo chmod +x .devcontainer/scripts/*.sh
sudo chown -R $(whoami) $HOME

if [ -z "${VELOCITAS_OFFLINE}" ]; then
    echo "#######################################################"
    echo "### Install Prerequisites and Tools                 ###"
    echo "#######################################################"

    # Optionally install the cmake for vcpkg
    .devcontainer/scripts/reinstall-cmake.sh ${REINSTALL_CMAKE_VERSION_FROM_SOURCE}

    # Install python, conan and ccache
    sudo apt-get update
    sudo apt-get install -y python3
    sudo apt-get install -y python3-distutils
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | sudo python3
    sudo apt-get -y install --no-install-recommends ccache

    build_arch=$(arch)

    # ensure we can always build for an arm target
    if [ "${build_arch}" != "aarch64" ]; then
        sudo apt-get install -y gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
    fi

    pip3 install -r ./requirements.txt

    # Install static analyzer tools
    sudo apt-get install -y cppcheck clang-format-14 clang-tidy-14
    sudo update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-14 100
    sudo update-alternatives --install /usr/bin/clang-tidy clang-tidy /usr/bin/clang-tidy-14 100

    if [ "${CODESPACES}" = "true" ]; then
        echo "#######################################################"
        echo "### Setup Access to Codespaces                      ###"
        echo "#######################################################"

        # Remove the default credential helper
        sudo sed -i -E 's/helper =.*//' /etc/gitconfig

        # Add one that just uses secrets available in the Codespace
        git config --global credential.helper '!f() { sleep 1; echo "username=${GITHUB_USER}"; echo "password=${MY_GH_TOKEN}"; }; f'
    fi

    echo "#######################################################"
    echo "### VADF package status                             ###"
    echo "#######################################################"
    velocitas upgrade --dry-run
fi

echo "#######################################################"
echo "### Install Dependencies                            ###"
echo "#######################################################"
velocitas exec build-system install -r 2>&1 | tee -a $HOME/install_dependencies.log
# Install dependencies for target release build
velocitas exec build-system install -r -x aarch64

# Don't let container creation fail if lifecycle management fails
echo "Done!"
