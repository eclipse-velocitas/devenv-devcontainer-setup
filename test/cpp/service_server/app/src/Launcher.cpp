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

#include <services/hornservice/HornserviceServiceServerFactory.h>
#include <services/seats/SeatsServiceServerFactory.h>
#include <services/val/ValServiceServerFactory.h>
#include <services/vcsmotortrqmngservice/VcsmotortrqmngserviceServiceServerFactory.h>
#include <services/vcsptcpbylimservice/VcsptcpbylimserviceServiceServerFactory.h>

#include <memory>
#include <thread>

#include "HornserviceServiceServiceImpl.h"
#include "SeatsServiceImpl.h"
#include "VCSMotorTrqMngServiceServiceImpl.h"
#include "VCSPtCpbyLimServiceServiceImpl.h"
#include "ValServiceImpl.h"
#include "sdk/middleware/Middleware.h"

using namespace velocitas;

int main(int argc, char** argv) {
    auto seatsImpl = std::make_shared<SeatsService>();

    auto seatServer =
        SeatsServiceServerFactory::create(Middleware::getInstance(), seatsImpl);

    std::thread seatThread(seatServer->Wait());

    auto hornImpl = std::make_shared<HornService>();

    auto hornserver =
        HornserviceServiceServerFactory::create(Middleware::getInstance(), hornImpl);

    std::thread hornThread(hornserver->Wait());

    auto valImpl = std::make_shared<VALService>();

    auto valServer = ValServiceServerFactory::create(Middleware::getInstance(), valImpl);

    std::thread valThread(valServer->Wait());

    auto motorcontrolImpl = std::make_shared<VCSMotorTrqMngServiceService>();

    auto motorcontrolServer = VcsmotortrqmngserviceServiceServerFactory::create(
        Middleware::getInstance(), motorcontrolImpl);

    std::thread motorcontrolThread(motorcontrolServer->Wait());

    auto capacitycontrolImpl = std::make_shared<VCSPtCpbyLimServiceService>();

    auto capacitycontrolServer = VcsptcpbylimserviceServiceServerFactory::create(
        Middleware::getInstance(), capacitycontrolImpl);

    std::thread capacitycontrolThread(capacitycontrolServer->Wait());

    seatThread.detach();
    hornThread.detach();
    valThread.detach();
    motorcontrolThread.detach();
    capacitycontrolThread.detach();

    return 0;
}
