import random
import struct
import time
from socket import *

import yaml
from typeguard import typechecked

from rpc_pb2 import Request, Response, AddRequest, AddResponse, SubRequest, SubResponse
from service import Service


class ClientStub(Service):

    def __init__(self, host, port, time_out=30):
        self.host = host
        self.port = port
        with open('config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        self.registry_host = config["Registry"]["host"]
        self.registry_port = config["Registry"]["port"]
        self.timeout = time_out

    def __connect(self, host, port, request, response):
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((host, port))
                s.settimeout(self.timeout)
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
            return response

    def __discover(self, service_name):
        request = Request(type='discover', service_name=service_name, )
        response = Response()
        response = self.__connect(self.registry_host, self.registry_port, request, response)
        # 超时
        if response.type == 'timeout':
            print("Attempting to reconnect...")
            time.sleep(2)
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
        # 这里要注意：因为有些服务器是监听的'0.0.0.0', 而这不是一个有效的ip地址，所以应该做一下处理(这里简单化处理为本机地址)
        server.host = '127.0.0.1'
        response = self.__connect(server.host, server.port, request, response)
        # 超时
        if response.type == 'timeout':
            print("Attempting to reconnect...")
            time.sleep(2)
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
