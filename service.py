from abc import ABC, abstractmethod
from rpc_pb2 import AddRequest, AddResponse

class Service(ABC):
    
    @abstractmethod
    def add(self, AddRequest) -> AddResponse:
        pass
