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

#include "${{ service_include_dir }}/${{ service_name_camel_case }}ServiceServerFactory.h"
#include "sdk/middleware/Middleware.h"
#include "sdk/Logger.h"

#include <grpcpp/ext/proto_server_reflection_plugin.h>
#include <grpcpp/grpcpp.h>
#include <grpcpp/health_check_service_interface.h>

namespace velocitas {

std::unique_ptr<grpc::Server> ${{ service_name_camel_case }}ServiceServerFactory::create(
    Middleware&                                                      middleware,
    std::shared_ptr<${{ package_id }}::${{ service_name }}::Service>&& service) {
    const auto serviceLocation = middleware.getServiceLocation("${{ service_name }}");

    grpc::EnableDefaultHealthCheckService(true);
    grpc::reflection::InitProtoReflectionServerBuilderPlugin();
    grpc::ServerBuilder builder;
    // Listen on the given address without any authentication mechanism.
    builder.AddListeningPort(serviceLocation, grpc::InsecureServerCredentials());
    // Register "service" as the instance through which we'll communicate with
    // clients. In this case it corresponds to an *synchronous* service.
    builder.RegisterService(service.get());
    // Finally assemble the server.
    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    velocitas::logger().info("Server ${{ package_id }}::${{ service_name }} listening on {}", serviceLocation);

    return server;
}

} // namespace velocitas
