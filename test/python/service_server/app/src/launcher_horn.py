import grpc
from hornservice_service_sdk.HornServiceServiceServerFactory import (
    HornServiceServiceServerFactory,
)
from HornServiceServiceImpl import HornServiceService
from test_middleware import TestMiddleware, TestServerServiceLocator
from velocitas_sdk.base import Middleware


def create_horn_server(middleware: Middleware) -> grpc.Server:
    servicer = HornServiceService()

    return HornServiceServiceServerFactory.create(
        middleware,
        servicer,
    )


if __name__ == "__main__":
    middleware_server_mock = TestMiddleware(TestServerServiceLocator())

    server = create_horn_server(middleware_server_mock)
    server.start()
    server.wait_for_termination()
