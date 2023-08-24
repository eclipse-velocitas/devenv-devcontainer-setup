#!/bin/bash
# Copyright (c) 2022-2023 Robert Bosch GmbH
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

echo "#######################################################"
echo "### Auto-Upgrade CLI                                ###"
echo "#######################################################"

AUTHORIZATION_HEADER=""
if [ "${GITHUB_API_TOKEN}" != "" ]; then
  AUTHORIZATION_HEADER="-H \"Authorization: Bearer ${GITHUB_API_TOKEN}\""
fi

# Get latest available version
LATEST_VERSION=$(curl -s -L \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  ${AUTHORIZATION_HEADER} \
  https://api.github.com/repos/eclipse-velocitas/cli/releases/latest | jq -r .name)

# Get installed version
INSTALLED_VERSION=v$(velocitas --version | sed -E 's/velocitas-cli\/(\w+.\w+.\w+).*/\1/')

if [ "$LATEST_VERSION" != "$INSTALLED_VERSION" ]; then
  echo "> Upgrading CLI..."
  CLI_ASSET_NAME=velocitas-linux-$(arch | sed 's/amd64/x64/g' | sed 's/aarch64/arm64/g')
  CLI_INSTALL_PATH=/usr/bin/velocitas
  CLI_DOWNLOAD_URL="https://github.com/eclipse-velocitas/cli/releases/download/${LATEST_VERSION}/${CLI_ASSET_NAME}"

  echo "> Downloading Velocitas CLI from ${CLI_DOWNLOAD_URL}"
  sudo curl -s -L ${CLI_DOWNLOAD_URL} -o "${CLI_INSTALL_PATH}"
  sudo chmod +x "${CLI_INSTALL_PATH}"
else
  echo "> Up to date!"
fi

echo "> Using CLI: $(velocitas --version)"

echo "#######################################################"
echo "### Run VADF Lifecycle Management                   ###"
echo "#######################################################"
# needed to get rid of old leftovers
sudo rm -rf ~/.velocitas
velocitas init
velocitas sync

sudo chmod +x .devcontainer/scripts/*.sh
sudo chown -R $(whoami) $HOME

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
echo "### Init submodules                                 ###"
echo "#######################################################"
git config --global --add safe.directory "*"
git submodule update --init

echo "#######################################################"
echo "### Install Dependencies                            ###"
echo "#######################################################"
./install_dependencies.sh 2>&1 | tee -a $HOME/install_dependencies.log

echo "#######################################################"
echo "### VADF package status                             ###"
echo "#######################################################"
velocitas upgrade --dry-run

# Don't let container creation fail if lifecycle management fails
echo "Done!"
