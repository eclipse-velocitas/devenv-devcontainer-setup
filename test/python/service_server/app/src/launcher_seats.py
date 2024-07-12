import grpc
from seats_service_sdk.SeatsServiceServerFactory import SeatsServiceServerFactory
from SeatsServiceImpl import SeatsService
from test_middleware import TestMiddleware, TestServerServiceLocator
from velocitas_sdk.base import Middleware


def create_seats_server(middleware: Middleware) -> grpc.Server:
    servicer = SeatsService()

    return SeatsServiceServerFactory.create(
        middleware,
        servicer,
    )


if __name__ == "__main__":
    middleware_server_mock = TestMiddleware(TestServerServiceLocator())

    server = create_seats_server(middleware_server_mock)
    server.start()
    server.wait_for_termination()
