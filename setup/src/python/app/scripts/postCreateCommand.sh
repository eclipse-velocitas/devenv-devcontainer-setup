#!/bin/bash
# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
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

echo "#######################################################"
echo "### Install python requirements                     ###"
echo "#######################################################"
# Update pip before installing requirements
pip3 install --upgrade pip
REQUIREMENTS="./requirements.txt"
if [ -f $REQUIREMENTS ]; then
    pip3 install -r $REQUIREMENTS
fi
REQUIREMENTS="./app/requirements-links.txt"
if [ -f $REQUIREMENTS ]; then
    pip3 install -r $REQUIREMENTS
fi
# Dependencies for the app
REQUIREMENTS="./app/requirements.txt"
if [ -f $REQUIREMENTS ]; then
    pip3 install -r $REQUIREMENTS
fi

# Dependencies for unit and integration tests
REQUIREMENTS="./app/tests/requirements.txt"
if [ -f $REQUIREMENTS ]; then
    pip3 install -r $REQUIREMENTS
fi

# add repo to git safe.directory
REPO=$(pwd)
git config --global --add safe.directory $REPO

echo "#######################################################"
echo "### VADF package status                             ###"
echo "#######################################################"
velocitas upgrade --dry-run

# Don't let container creation fail if lifecycle management fails
echo "Done!"
