# gRPC Interface Support

Extends Velocitas applications and services with the ability to describe a dependency to a gRPC service via its interface definition in a proto file.

The component provides CLI exec targets which can generate service client SDKs and service server SDKs for all dependent services which will be made available for the application to use via a simple factory interface.

## Generation

Run the exposed `generate-sdk` program via Velocitas CLI to generate a service SDK for usage within either client or server applications.
e.g.

```
velocitas exec grpc-interface-support generate-sdk
```

Depending on the interfaces defined in the `AppManifest` file, either classes and SDKs for client, server or both are generated.

For generating a client SDK:
```json
{
    "manifestVersion": "v3",
    "name": "App",
    "interfaces": [
        {
            "type": "grpc-interface",
            "config": {
                "src": "<uri_to_proto_file>",
                "required": {}
            }
        }
    ]
}
```

For generating a server SDK:
```json
{
    "manifestVersion": "v3",
    "name": "App",
    "interfaces": [
        {
            "type": "grpc-interface",
            "config": {
                "src": "<uri_to_proto_file>",
                "provided": {}
            }
        }
    ]
}
```

For generating both:
```json
{
    "manifestVersion": "v3",
    "name": "App",
    "interfaces": [
        {
            "type": "grpc-interface",
            "config": {
                "src": "<uri_to_proto_file>",
                "required": {},
                "provided": {}
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

When generating a server SDK, in addition to the SDK package, 2 files are auto generated into your application's source directory:

* `<Service>ServerImpl.h` contains class definition and method declarations for implementing the server. This file is continuously auto-generated! To add custom methods place them within the `// <user-defined>` block.
* `<Service>ServerImpl.cc` contains method definitions for all server methods, defaulting to `UNIMPLEMENTED`. This file is only generated **once** if it does not exist.

Why is the header continuously re-generated and the cpp file is not? - The header always contains up-to-date method declarations reflecting the proto state. If they change, the source code, which most likely has more LoC, needs to be adapted manually.

To instantiate a server with your custom implementation, use the provided factory API to interface with the Velocitas core SDK:

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
