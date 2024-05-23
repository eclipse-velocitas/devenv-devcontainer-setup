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

#include "SampleApp.h"

#include "sdk/middleware/Middleware.h"
#include "services/seats/SeatsServiceClientFactory.h"
#include "services/seats/seats.grpc.pb.h"

#include <iostream>

using namespace velocitas;

int main(int argc, char** argv) {
    auto seatService =
        SeatsServiceClientFactory::create(Middleware::getInstance());

    ::grpc::ClientContext context;
    ::sdv::edge::comfort::seats::v1::MoveRequest request;
    ::sdv::edge::comfort::seats::v1::MoveReply response;
    auto status = seatService->Move(&context, request, &response);

    std::cout << "gRPC Server returned code: " << status.error_code() << std::endl;
    std::cout << "gRPC error message: " << status.error_message().c_str() << std::endl;

    if (status.error_code () == ::grpc::StatusCode::UNIMPLEMENTED) {
        return 0;
    }

    return 1;
}
