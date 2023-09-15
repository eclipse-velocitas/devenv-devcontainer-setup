# gRPC Interface Support

Extends Velocitas applications and services with the ability to describe a dependency to a gRPC service via its interface definition in a proto file.

The component provides CLI exec targets which will generate service client SDKs for all dependent services which will be made available for the application to use via a simple factory interface.
