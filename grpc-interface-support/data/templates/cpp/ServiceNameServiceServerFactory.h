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

#ifndef VELOCITAS_SERVICE_${{ service_name }}_SERVER_FACTORY_H
#define VELOCITAS_SERVICE_${{ service_name }}_SERVER_FACTORY_H


#include "services/${{ service_name_lower }}/${{ service_name_lower }}.grpc.pb.h"

#include <grpcpp/server.h>
#include <memory>

namespace velocitas {

class Middleware;

/**
 * @brief Factory which facilitates creation of ${{ service_name_camel_case }} servers.
 *
 */
class ${{ service_name_camel_case }}ServiceServerFactory {
public:
    static std::unique_ptr<grpc::Server> create(Middleware&                                                      middleware,
                std::shared_ptr<${{ package_id }}::${{ service_name }}::Service>&& service);

    ${{ service_name_camel_case }}ServiceServerFactory() = delete;
};

} // namespace velocitas

#endif // VELOCITAS_SERVICE_${{ service_name }}_SERVER_FACTORY_H
