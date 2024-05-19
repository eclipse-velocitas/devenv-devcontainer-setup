/**
 * Copyright (c) 2024 Contributors to the Eclipse Foundation
 *
 * This program and the accompanying materials are made available under the
 * terms of the Apache License, Version 2.0 which is available at
 * https://www.apache.org/licenses/LICENSE-2.0.
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "sdk/middleware/Middleware.h"
#include "services/seats/SeatsServiceServerFactory.h"
#include "SeatsServiceImpl.h"

#include <memory>

using namespace velocitas;

int main(int argc, char** argv) {
    auto seatsImpl = std::make_shared<SeatsService>();

    auto seatServer =
        SeatsServiceServerFactory::create(Middleware::getInstance(), seatsImpl);

    seatServer->Wait();
    return 0;
}
