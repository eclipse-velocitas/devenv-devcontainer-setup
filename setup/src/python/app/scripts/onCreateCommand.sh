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

# Build NodeRed
ROOT_DIRECTORY=$( realpath "$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )/../.." )
cd $ROOT_DIRECTORY/nodeRed
# To remove first line which comes from velocitas sync command
FIRST_FLOWS_LINE=$(head -n 1 flows.json| cut -c 4-)
if [[ $FIRST_FLOWS_LINE == This* ]];then
   echo "Trim flows.json, by deleting the maintenance hint."
   tail +2 flows.json > tmp.flows && mv tmp.flows flows.json
fi
docker build -t nodered .

# Don't let container creation fail if lifecycle management fails
echo "Done!"
