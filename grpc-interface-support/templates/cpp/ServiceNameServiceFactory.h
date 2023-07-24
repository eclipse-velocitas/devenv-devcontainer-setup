/**
 * Copyright (c) 2023 Contributors to the Eclipse Foundation
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

#ifndef VELOCITAS_SERVICE_${{ service_name }}_H
#define VELOCITAS_SERVICE_${{ service_name }}_H

#include "services/${{ service_name_lower }}/${{ service_name_lower }}.grpc.pb.h"

#include <memory>

namespace velocitas {

class Middleware;

class ${{ service_name_camel_case }}Service : public ${{ package_id }}::Service {
public:
    ${{ service_name_camel_case }}Service();

    virtual ~${{ service_name_camel_case }}Service();
};

} // namespace velocitas

#endif // VELOCITAS_SERVICE_${{ service_name }}_H
