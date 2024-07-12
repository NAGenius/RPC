import struct
import threading
import time
from rpc_pb2 import Request, Response, AddRequest, AddResponse
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
            host=self.host,
            port=self.port,
        )
        response = Response()
        response = self.__connect(self.registry_host, self.registry_port, request, response)
        # TODO: 出错处理
    
    def __handle_request(self, conn, addr):
        with conn:
            while True:
                length, = struct.unpack('!I', conn.recv(4))
                if not length:
                    break
                request = conn.recv(length)
                if not request:
                    break
                request_data = 
                
    
    def __run_server(self):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(10)
            print(f'Server is listening on {self.host}:{self.port}')
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.__handle_request, args=(conn, addr)).start()
    
    def __send_heartbeat(self):
        while True:
            time.sleep(self.heartbeat_interval)
            request = Request(
                type='heartbeat',
                host=self.host,
                port=self.port,
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
