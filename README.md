# Velocitas Package for DevContainer Setup

Repo for Devcontainer Configuration and vehicle model generation on container startup.

> [!IMPORTANT]
> We sucessfully migrated our C++ repositories to use version 2 of the [Conan package manager](https://conan.io/).
> Unfortunately, those changes are not backwards compatible. So, please be aware that versions >= 3.0.0 of this repository 
> are compatible with recent versions of the [C++ SDK](https://github.com/eclipse-velocitas/vehicle-app-cpp-sdk) (>= v0.7.0) 
> and [C++ App Template](https://github.com/eclipse-velocitas/vehicle-app-cpp-template), only.
>
> This is not relevant for the Python related template and SDK repositories.

## Components in this package

* [Basic Setup](./setup/README.md)
* [gRPC Interface Support](./grpc-interface-support/README.md)
* [Vehicle Signal Interface Support](./vehicle-model-lifecycle/README.md)
* [SDK Installer](./sdk-installer/README.md)
* [Conan Setup](./conan-setup/README.md)
