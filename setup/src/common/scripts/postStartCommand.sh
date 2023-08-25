#!/bin/bash
# Copyright (c) 2023 Robert Bosch GmbH
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

# Check for internet connection
wget -q --spider http://google.com
if [ $? -ne 0 ]; then
    echo "> No internet connection. Skipping Auto-Upgrade."
    exit 0
fi

AUTHORIZATION_HEADER=""
if [ "${GITHUB_API_TOKEN}" != "" ]; then
  AUTHORIZATION_HEADER="-H \"Authorization: Bearer ${GITHUB_API_TOKEN}\""
fi

ROOT_DIRECTORY=$( realpath "$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )/../.." )
DESIRED_VERSION=$(cat $ROOT_DIRECTORY/.velocitas.json | jq .cliVersion | tr -d '"')
DESIRED_VERSION_TAG=$(curl -s -L \
-H "Accept: application/vnd.github+json" \
-H "X-GitHub-Api-Version: 2022-11-28" \
${AUTHORIZATION_HEADER} \
https://api.github.com/repos/eclipse-velocitas/cli/releases/tags/${DESIRED_VERSION} | jq -r .name)

if [ "$DESIRED_VERSION" != "$DESIRED_VERSION_TAG" ]; then
  echo "> Can't find desired Velocitas CLI version: $DESIRED_VERSION"
  exit 1
fi

# Get installed version
INSTALLED_VERSION=v$(velocitas --version | sed -E 's/velocitas-cli\/(\w+.\w+.\w+).*/\1/')

if [ "$DESIRED_VERSION" != "$INSTALLED_VERSION" ]; then
  echo "> Upgrading CLI..."
  CLI_ASSET_NAME=velocitas-linux-$(arch | sed 's/amd64/x64/g' | sed 's/aarch64/arm64/g')
  CLI_INSTALL_PATH=/usr/bin/velocitas
  CLI_DOWNLOAD_URL="https://github.com/eclipse-velocitas/cli/releases/download/${DESIRED_VERSION}/${CLI_ASSET_NAME}"

  echo "> Downloading Velocitas CLI from ${CLI_DOWNLOAD_URL}"
  sudo curl -s -L ${CLI_DOWNLOAD_URL} -o "${CLI_INSTALL_PATH}"
  sudo chmod +x "${CLI_INSTALL_PATH}"
else
  echo "> Up to date!"
fi

echo "> Using CLI: $(velocitas --version)"
