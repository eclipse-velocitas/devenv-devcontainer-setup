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

#ifndef VELOCITAS_SERVICE_${{ service_name }}_CLIENT_FACTORY_H
#define VELOCITAS_SERVICE_${{ service_name }}_CLIENT_FACTORY_H

#include "services/${{ service_name_lower }}/${{ service_name_lower }}.grpc.pb.h"

#include <memory>

namespace velocitas {

class Middleware;

/**
 * @brief Factory which facilitates creation of ${{ service_name_camel_case }}.
 *
 */
class ${{ service_name_camel_case }}ServiceClientFactory {
public:
    /**
     * @brief Create a new ${{ service_name_camel_case }} client.
     *
     * @param middleware  The middleware used by the Velocitas application.
     *
     * @return A new ${{ service_name_camel_case }} instance.
     */
    static std::shared_ptr<${{ package_id }}::${{ service_name }}::Stub> create(Middleware& middleware);

    ${{ service_name_camel_case }}ServiceClientFactory() = delete;
};

} // namespace velocitas

#endif // VELOCITAS_SERVICE_${{ service_name }}_CLIENT_FACTORY_H
