from rpc_pb2 import AddRequest, AddResponse, SubRequest, SubResponse
import argparse

from serverstub import ServerStub
from service import Service


class MyService(Service):

    def add(self, arg: AddRequest) -> AddResponse:
        return AddResponse(sum=arg.a + arg.b)

    def sub(self, arg: SubRequest) -> SubResponse:
        return SubResponse(diff=arg.a - arg.b)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RPC Server', add_help=False)
    # required
    parser.add_argument('-i', '--ip', metavar='', type=str, required=False, default='127.0.0.1',
                        help='Listening IP address.')
    parser.add_argument('-p', '--port', metavar='', type=int, required=False, default=50000,
                        help='Listening port number.')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    args = parser.parse_args()

    services = MyService()
    server = ServerStub(args.ip, args.port)
    server.add_service('add', services.add)
    server.add_service('sub', services.sub)
    server.start()
