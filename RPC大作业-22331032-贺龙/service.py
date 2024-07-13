from abc import ABC, abstractmethod
from rpc_pb2 import AddRequest, AddResponse, SubRequest, SubResponse


class Service(ABC):

    @abstractmethod
    def add(self, arg: AddRequest) -> AddResponse:
        pass

    @abstractmethod
    def sub(self, arg: SubRequest) -> SubResponse:
        pass
