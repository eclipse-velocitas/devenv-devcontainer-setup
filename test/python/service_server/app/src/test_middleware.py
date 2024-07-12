from typing import Optional

from velocitas_sdk.base import Middleware, ServiceLocator

SERVICE_ADRESS = "127.0.0.1:1234"


class TestServerServiceLocator(ServiceLocator):
    def get_service_location(self, service_name: str) -> str:
        return SERVICE_ADRESS

    def get_metadata(self, service_name: Optional[str] = None):
        pass


class TestMiddleware(Middleware):
    def __init__(self, serviceLocator: ServiceLocator) -> None:
        self.service_locator = serviceLocator

    async def start(self):
        pass

    async def wait_until_ready(self):
        pass

    async def stop(self):
        pass
