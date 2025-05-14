# gRPC Interface Support

Extends Velocitas applications with the ability to consume or provide gRPC services by just describing that dependency via its interface definition in a proto file.

The component provides CLI exec targets which can generate service consumer (i.e. client) SDKs and service provider (i.e. server) SDKs for all dependent services which will be made available for the application to use via a simple factory interface.

## Generation

Run the exposed `generate-sdk` program via Velocitas CLI to generate a service SDK for usage within either client or server applications.
e.g.

```
velocitas exec grpc-interface-support generate-sdk
```

Depending on the interfaces defined in the `AppManifest` file, either classes and SDKs for client, server or both are generated.


| parameters                          | meaning                                                          | client SDK                       | server SDK                       | local proto file (absolute path) | local proto file (relative path) | archive                          | downloadable file (raw not blob) |
| -------------------------------- | ---------------------------------------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- |
| src                              | The source (absolute or relative) to the proto files (dir, zip, file, link) | /home/user/proto_file.proto       | /home/user/proto_file.proto       | /home/user/proto_file.proto       | proto_file.proto (located under workspace of template repository) | https://github.com/project/release.zip | https://github.com/project/raw/proto_file.proto |
| required                         | The functions that the client uses                             | { client_function1(), client_function2(), ... }                 | not defined                      | see sdk examples                 | see sdk examples                 | see sdk examples                 | see sdk examples                 |
| provided                         | Set if the server code shall be generated to {}                 | not defined                      | {}                               | see sdk examples                 | see sdk examples                 | see sdk examples                 | see sdk examples                 |
| protoIncludeDir                  | The path to some imports in the protot files (default parent folder) | path_to_imports                  | path_to_imports                  | path_to_imports                  | path_to_imports                  | path_to_imports                  | path_to_imports                  |
| pathInZip                        | If you have multiple folders in a zip and just want one to be generated | undefined                        | undefined                        | undefined                        | undefined                        | rel_path_archive                | undefined                        |

Example json:
```json
{
    "manifestVersion": "v3",
    "name": "App",
    "interfaces": [
        {
            "type": "grpc-interface",
            "config": {
                "src": "home/user/proto_file.proto",
                "protoIncludeDir": "<path_to_imports>",
                "required": {},
                "provided": {},
            }
        }
    ]
}
```

## Usage

### Client

To instantiate a client and call a method on the client instance, use the provided factory API to interface with the Velocitas core SDK:

```cpp
#include "sdk/middleware/Middleware.h"
#include "services/seats/SeatsServiceClientFactory.h"
#include "services/seats/seats.grpc.pb.h"

using namespace velocitas;

int main(int argc, char** argv) {
    auto seatService =
        SeatsServiceClientFactory::create(Middleware::getInstance());

    ::grpc::ClientContext context;
    ::sdv::edge::comfort::seats::v1::MoveRequest request;
    ::sdv::edge::comfort::seats::v1::MoveReply response;
    auto status = seatService->Move(&context, request, &response);
    return status.ok() ? 0 : 1;
}
```

### Server

When generating a server SDK, in addition to the SDK package, one or more files (depending on the target language) are auto generated into your application's source directory. To instantiate a server with your custom implementation, use the provided factory API to interface with the Velocitas core SDK.

***C++***

Generated files:

* `<Service-Name>ServiceImpl.h` contains class definition and method declarations for implementing the server. This file is continuously auto-generated! To add custom methods place them within the `// <user-defined>` block.
* `<Service-Name>ServiceImpl.cpp` contains method definitions for all server methods, defaulting to `UNIMPLEMENTED`. This file is only generated **once** if it does not exist.

```cpp
#include "sdk/middleware/Middleware.h"
#include "services/seats/SeatsServiceServerFactory.h"
#include "SeatsServiceServer.h"

#include <memory>

using namespace velocitas;

int main(int argc, char** argv) {
    auto seatsImpl = std::make_shared<SeatsService>();

    auto seatServer =
        SeatsServiceServerFactory::create(Middleware::getInstance(), seatsImpl);

    seatServer->Wait();
    return 0;
}

```

***Python***

Generated files:

* `<Service-Name>ServiceStub.py` contains class definition and method declarations for implementing the server. This file is continuously auto-generated! To add custom methods place them inside the `<Service-Name>ServiceImpl.py` class.
* `<Service-Name>ServiceImpl.py` contains method definitions for all server methods, defaulting to `UNIMPLEMENTED`. This file is only generated **once** if it does not exist.

```python
from velocitas_sdk.config import middleware
from seats_service_sdk.seats_pb2_grpc import SeatsServicer
from seats_service_sdk.SeatsServiceServerFactory import SeatsServiceServerFactory
from SeatsServiceImpl import SeatsService

async def on_start(self):
    seatsService = SeatsService()
    server = SeatsServiceServerFactory.create(
        seatsService,
        middleware, # Create your own middleware sub class
    )

    server.start()
    server.wait_for_termination()
```

**Why is one file continuously re-generated and the another file is not?** - One file always contains up-to-date method declarations reflecting the proto state. If they change, the source code, which most likely has more LoC, needs to be adapted manually.
