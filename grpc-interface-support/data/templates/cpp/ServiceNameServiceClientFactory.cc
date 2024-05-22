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

#include "services/${{ service_name_lower }}/${{ service_name_camel_case }}ServiceClientFactory.h"

#include "sdk/middleware/Middleware.h"

#include <grpcpp/channel.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

namespace velocitas {

std::shared_ptr<${{ package_id }}::${{ service_name }}::Stub>
${{ service_name_camel_case }}ServiceClientFactory::create(Middleware& middleware) {
    auto channel = grpc::CreateChannel(middleware.getServiceLocation("${{ service_name }}"), grpc::InsecureChannelCredentials());
    auto stub    = std::make_shared<${{ package_id }}::${{ service_name }}::Stub>(channel);
    return stub;
}

} // namespace velocitas
