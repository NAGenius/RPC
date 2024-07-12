import struct
import threading
import time
from socket import *

import yaml

from rpc_pb2 import Request, Response, Server


class ServerStub:

    def __init__(self, host, port, heartbeat_interval=10):
        self.host = host
        self.port = port
        self.services = {}
        with open('config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        self.registry_host = config["Registry"]["host"]
        self.registry_port = config["Registry"]["port"]

        self.lock = threading.Lock()
        self.heartbeat_interval = heartbeat_interval

    def add_service(self, service_name, service):
        self.services[service_name] = service
        # 注册服务
        self.__register_service(service_name)

    def __connect(self, host, port, request, response):
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((host, port))
                request_data = request.SerializeToString()
                print(request)
                s.sendall(struct.pack('!I', len(request_data)) + request_data)
                length, = struct.unpack('!I', s.recv(4))
                response.ParseFromString(s.recv(length))
                return response
        except timeout as e:
            print(f'Connection to {host}:{port} timed out.')
            response.type = 'timeout'
            response.content = f'Error: {e}'

    def __register_service(self, service_name):
        request = Request(
            type='register',
            service_name=service_name,
            server=Server(host=self.host, port=self.port),
        )
        response = Response()
        response = self.__connect(self.registry_host, self.registry_port, request, response)
        # 超时/出错（注册失败）, 重新连接一次
        if response.type == 'timeout' or response.type == 'error':
            response = self.__connect(self.registry_host, self.registry_port, request, response)
            # 还是失败的话, 抛出错误
            if response.type == 'timeout' or response.type == 'error':
                raise Exception(response.content)

    def __handle_request(self, conn):
        with conn:
            while True:
                print(conn)
                length_prefix = conn.recv(4)
                if not length_prefix:
                    break
                length, = struct.unpack('!I', length_prefix)
                request_data = conn.recv(length)
                if not request_data:
                    break
                request = Request()
                request.ParseFromString(request_data)
                service_name = request.service_name
                print('ans', self.services[service_name](getattr(request, service_name)))
                if service_name in self.services:
                    try:
                        # FIXME: 这里用 getattr() 和 setattr() 函数还是有点不太理想
                        response = Response(type='success')
                        getattr(response, service_name).CopyFrom(
                            self.services[service_name](getattr(request, service_name)))
                    except Exception as e:
                        response = Response(
                            type='error',
                            content=str(e),
                        )
                else:
                    response = Response(
                        type='fail',
                        content=f'Function: {service_name} not found.',
                    )
                response_data = response.SerializeToString()
                print(response)
                conn.sendall(struct.pack('!I', len(response_data)) + response_data)

    def __run_server(self):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(10)
            print(f'Server is listening on {self.host}:{self.port}')
            while True:
                conn, addr = s.accept()
                print(f'server connected by {addr}')
                threading.Thread(target=self.__handle_request, args=(conn,)).start()

    def __send_heartbeat(self):
        while True:
            time.sleep(self.heartbeat_interval)
            request = Request(
                type='heartbeat',
                server=Server(host=self.host, port=self.port),
            )
            response = Response()
            response = self.__connect(self.registry_host, self.registry_port, request, response)
            # 超时/出错（注册失败）, 重新连接一次
            if response.type == 'timeout' or response.type == 'error':
                response = self.__connect(self.registry_host, self.registry_port, request, response)
                # 还是失败的话, 抛出错误
                if response.type == 'timeout' or response.type == 'error':
                    raise Exception(response.content)

    def start(self):
        threading.Thread(target=self.__run_server).start()
        threading.Thread(target=self.__send_heartbeat).start()
