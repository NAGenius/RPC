import argparse
import struct
import threading
from rpc_pb2 import Request, Response
from socket import *


class Registry:
    
    def __init__(self, host, port, heartbeat_interval=10):
        self.host = host
        self.port = port
        self.heartbeat_interval = heartbeat_interval
        self.servers = {}
        self.lock = threading.Lock()
        
    def start(self):
        with socket(AF_INET, SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(10)
            print(f"Registry server is listening on {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                with conn:
                    self.__handle_request(conn)
                    
    def __handle_request(self, conn):
        length, = struct.unpack('!I', conn.recv(4))
        if not length:
            return
        request_data = conn.recv(length)
        if not request_data:
            return
        request = Request()
        request.ParseFromString(request_data)
        response = Response()
        if request.type == 'register':
            response = self.__register_service(request.service_name, request.server)
        elif request.type == 'heartbeat':
            response = self.__update_heartbeat(request.service_name, request.server)
        elif request.type == 'discover':
            response = self.__discover_service(request.service_name)
        response_data = response.SerializeToString()
        conn.sendall(struct.pack('!I', len(response_data)) + response_data)
            
    def __register_service(self, service_name, server):
        try:
            with self.lock:
                if service_name not in self.servers:
                    self.servers[service_name] = []
                self.servers[service_name].append(server)
                print(f"Register service: {service_name} from {server.host}:{server.port}")
                response = Response(
                    type='success',
                    content=f'{service_name} is registered successfully.'
                )
                return response
        except Exception as e:
            print(e)
            response = Response(
                type='error',
                content=f'Error: {e}'
            )
            return response
    
    def __update_heartbeat(self, service_name, server):
        with self.lock:
            servers = self.servers.get(service_name, [])
            for s in servers:
                if s.host == server.host and s.port == server.port:
                    response = Response(
                        type='alive',
                        content=f'service {service_name} on {server.host}:{server.port} is alive.'
                    )
                    return response
            response = Response(
                type='dead',
                content=f'service {service_name} on {server.host}:{server.port} is dead.'
            )
            return response
    
    def __discover_service(self, service_name):
        with self.lock:
            servers = self.servers.get(service_name, [])
        
        if not servers:
            response = Response(
                type='fail',
                content=f'There is no server that supports this service: {service_name}.'
            )
            return response
        
        response = Response(
            type='success',
            servers=servers
        )
        return response
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RPC Registry', add_help=False)
    # required
    parser.add_argument('-i', '--ip', metavar='', type=str, required=False, default='127.0.0.1',
                        help='Listening IP address.')
    parser.add_argument('-p', '--port', metavar='', type=int, required=False, default=54321,
                        help='Listening port number.')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    args = parser.parse_args()
    
    registry = Registry(args.ip, args.port)
    registry.start()
    