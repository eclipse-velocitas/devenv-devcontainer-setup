/**
 * Copyright (c) 2023-2024 Contributors to the Eclipse Foundation
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

#include <kuksa/val/v1/val.grpc.pb.h>
#include <sdk/middleware/Middleware.h>
#include <services/hornservice/HornserviceServiceClientFactory.h>
#include <services/hornservice/horn.grpc.pb.h>
#include <services/seats/SeatsServiceClientFactory.h>
#include <services/seats/seats.grpc.pb.h>
#include <services/val/ValServiceClientFactory.h>
#include <services/vcsmotortrqmngservice/VcsmotortrqmngserviceServiceClientFactory.h>
#include <services/vcsmotortrqmngservice/motorcontrol.grpc.pb.h>
#include <services/vcsptcpbylimservice/VcsptcpbylimserviceServiceClientFactory.h>
#include <services/vcsptcpbylimservice/capacitylimit.grpc.pb.h>

#include <iostream>

#include "SampleApp.h"

using namespace velocitas;

int main(int argc, char** argv) {
    auto seatService =
        SeatsServiceClientFactory::create(Middleware::getInstance());

    auto hornService = HornserviceServiceClientFactory::create(Middleware::getInstance());

    auto valService = ValServiceClientFactory::create(Middleware::getInstance());

    auto motorcontrolService =
        VcsmotortrqmngserviceServiceClientFactory::create(Middleware::getInstance());

    auto capacityService =
        VcsptcpbylimserviceServiceClientFactory::create(Middleware::getInstance());

    ::grpc::ClientContext context;
    ::sdv::edge::comfort::seats::v1::MoveRequest move_request;
    ::sdv::edge::comfort::seats::v1::MoveReply move_response;
    auto status = seatService->Move(&context, move_request, &move_response);

    std::cout << "gRPC Server returned code: " << status.error_code() << std::endl;
    std::cout << "gRPC error message: " << status.error_message().c_str() << std::endl;

    if (status.error_code() != ::grpc::StatusCode::UNIMPLEMENTED)
    {
       return 1;
    }

    ::bcm::horn::v1::StartRequest start_request;
    ::bcm::horn::v1::StartResponse start_response;

    status = hornService->Start(&context, start_request, &start_response);

    std::cout << "gRPC Server returned code: " << status.error_code() << std::endl;
    std::cout << "gRPC error message: " << status.error_message().c_str() << std::endl;

    if (status.error_code() != ::grpc::StatusCode::UNIMPLEMENTED)
    {
       return 1;
    }

    ::kuksa::val::v1::GetRequest get_reqeuest;
    ::kuksa::val::v1::GetResponse get_response;

    status = valService->Get(&context, get_reqeuest, &get_response);

    std::cout << "gRPC Server returned code: " << status.error_code() << std::endl;
    std::cout << "gRPC error message: " << status.error_message().c_str() << std::endl;

    if (status.error_code() != ::grpc::StatusCode::UNIMPLEMENTED)
    {
       return 1;
    }

    ::vcs::powertrain::v1::SetMCUCtrlReqRequest set_mcu_request;
    ::vcs::powertrain::v1::SetMCUCtrlReqResponse set_mcu_response;

    status = motorcontrolService->SetMCUCtrlReq(&context, set_mcu_request, &set_mcu_response);

    std::cout << "gRPC Server returned code: " << status.error_code() << std::endl;
    std::cout << "gRPC error message: " << status.error_message().c_str() << std::endl;

    if (status.error_code() != ::grpc::StatusCode::UNIMPLEMENTED)
    {
       return 1;
    }

    : vcs::powertrain::v1::NtfPtPwrLimRequest pwr_lim_request;
    ::vcs::powertrain::v1::NtfPtPwrLimResponse pwr_lim_response;

    status = capacityService->NtfPtPwrLim(&context, pwr_lim_request, &pwr_lim_response);

    std::cout << "gRPC Server returned code: " << status.error_code() << std::endl;
    std::cout << "gRPC error message: " << status.error_message().c_str() << std::endl;

    if (status.error_code() != ::grpc::StatusCode::UNIMPLEMENTED)
    {
       return 1;
    }

    return 0;
}
