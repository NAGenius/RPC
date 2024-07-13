import random
import struct
from socket import *

import yaml
from typeguard import typechecked

from rpc_pb2 import Request, Response, AddRequest, AddResponse, SubRequest, SubResponse
from service import Service


class ClientStub(Service):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        with open('config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        self.registry_host = config["Registry"]["host"]
        self.registry_port = config["Registry"]["port"]

    def __connect(self, host, port, request, response):
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((host, port))
                print(request)
                request_data = request.SerializeToString()
                s.sendall(struct.pack('!I', len(request_data)) + request_data)
                length, = struct.unpack('!I', s.recv(4))
                response.ParseFromString(s.recv(length))
                return response
        except timeout as e:
            print(f'Connection to {host}:{port} timed out.')
            response.type = 'timeout'
            response.content = f'Error: {e}'

    def __discover(self, service_name):
        request = Request(type='discover', service_name=service_name, )
        response = Response()
        response = self.__connect(self.registry_host, self.registry_port, request, response)
        # 超时
        if response.type == 'timeout':
            response = self.__connect(self.registry_host, self.registry_port, request, response)
            # 还是失败的话, 抛出错误
            if response.type == 'timeout':
                raise Exception(response.content)
        # 出错（不存在该服务）
        elif response.type == 'fail':
            raise Exception(response.content)
        return response.servers

    def __call(self, service_name, request, response):
        servers = self.__discover(service_name)
        if not servers:
            pass
        # 采用随机选择策略实现负载均衡
        server = random.choice(servers)
        response = self.__connect(server.host, server.port, request, response)
        # 超时
        if response.type == 'timeout':
            response = self.__connect(self.registry_host, self.registry_port, request, response)
            # 还是失败的话, 抛出错误
            if response.type == 'timeout':
                raise Exception(response.content)
        # 出错（调用函数出错）
        elif response.type == 'fail':
            raise Exception(response.content)
        return response

    @typechecked
    def add(self, arg=AddRequest) -> AddResponse:
        request = Request(type='call', service_name='add', add=arg, )
        response = Response()
        response = self.__call('add', request, response)
        return response.add

    @typechecked
    def sub(self, arg=SubRequest) -> SubResponse:
        request = Request(type='call', service_name='sub', sub=arg, )
        response = Response()
        response = self.__call('sub', request, response)
        return response.sub
