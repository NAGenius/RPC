import struct
import threading
import time
from rpc_pb2 import Request, Response, Server
import yaml
from socket import *

class ServerStub():
    
    def __init__(self, host, port, heartbeat_interval=10):
        self.host = host
        self.port = port
        self.services = {}
        with open('config.yaml', 'r') as yamlfile:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)
        
        self.registry_host = config["Registry"]["host"]
        self.registry_port = config["Registry"]["port"]
        
        self.lock = threading.Lock()
        self.heartbeat_interval = heartbeat_interval
        
    def add_service(self, service_name, service):
        self.services[service_name] = service
        # 注册服务
        self.__register_service(service_name)
    
    def __connect(self, host, port, request, response):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((host, port))
            request_data = request.SerializeToString()
            s.sendall(struct.pack('!I', len(request_data)) + request_data)
            length, = struct.unpack('!I', s.recv(4))
            response.ParseFromString(s.recv(length))
            return response
    
    def __register_service(self, service_name):
        request = Request(
            type='register',
            server_name=service_name,
            server=Server(host=self.host, port=self.port),
        )
        response = Response()
        response = self.__connect(self.registry_host, self.registry_port, request, response)
        # TODO: 出错处理
    
    def __handle_request(self, conn):
        with conn:
            while True:
                length, = struct.unpack('!I', conn.recv(4))
                if not length:
                    break
                request_data = conn.recv(length)
                if not request_data:
                    break
                request = Request()
                request.ParseFromString(request_data)
                service_name = request.service_name
                if service_name in self.services:
                    try:
                        # FIXME: 这里用 getattr() 和 setattr() 函数还是有点不太理想
                        response = Response(type='success')
                        setattr(response, service_name, self.services[service_name](getattr(request, service_name)))
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
            # TODO: 对返回值进行处理
            pass
    
    def start(self):
        server = threading.Thread(target=self.__run_server)
        server.start()
        heartbeat = threading.Thread(target=self.__send_heartbeat)
        heartbeat.start()
