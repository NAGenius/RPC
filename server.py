

import argparse

from serverstub import ServerStub
from service import Service

class MyService(Service):
    
    def add(self, a: int, b: int) -> int:
        return a + b


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RPC Client', add_help=False)
    # required
    parser.add_argument('-i', '--ip', metavar='', type=str, required=False, default='0.0.0.0',
                        help='Listening IP address.')
    parser.add_argument('-p', '--port', metavar='', type=int, required=False, default=54321,
                        help='Listening port number.')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    args = parser.parse_args()
    
    services = MyService()
    server = ServerStub(args.ip, args.port)
    server.add_service('add', services.add)
    server.start()