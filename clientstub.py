import random
from socket import *
import struct
import yaml
from rpc_pb2 import Request, Response, AddRequest, AddResponse
from service import Service
from typeguard import typechecked


class ClientStub(Service):
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        with open('config.yaml', 'r') as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)
        
        self.registry_host = config["Registry"]["host"]
        self.registry_port = config["Registry"]["port"]
        
    def __connect(self, host, port, request, response):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((host, port))
            request_data = request.SerializeToString()
            s.sendall(struct.pack('!I', len(request_data)) + request_data)
            length, = struct.unpack('!I', s.recv(4))
            response.ParseFromString(s.recv(length))
            return response
        
    def __discover(self, service_name):
        request = Request(
            type='discover',
            service_name=service_name,
        )
        response = Response()
        response = self.__connect(self.registry_host, self.registry_port, request, response)
        return response.servers
    
    def __call(self, service_name, request, response):
        servers = self.__discover(service_name)
        if not servers:
            pass
        # 采用随机选择策略实现负载均衡
        server = random.choice(servers)
        response = self.__connect(server.host, server.port, request, response)
        # TODO: 检查是否出错
        return response
        
    @typechecked
    def add(self, arg=AddRequest) -> AddResponse:
        request = Request(
            type='call',
            service_name='add',
            add=arg,
        )
        response = Response()
        response = self.__call('add', request, response)
        return response.sum
    
