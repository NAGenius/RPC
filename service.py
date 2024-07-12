from abc import ABC, abstractmethod

class Service(ABC):
    
    @abstractmethod
    def add(self, a: int, b: int) -> int:
        pass
