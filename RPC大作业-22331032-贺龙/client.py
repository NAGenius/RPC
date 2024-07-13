from clientstub import ClientStub
from rpc_pb2 import AddRequest, SubRequest
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RPC Client', add_help=False)
    # required
    parser.add_argument('-i', '--ip', metavar='', type=str, required=True, default='127.0.0.1',
                        help='The IP address of the server to be connected. Default: "127.0.0.1".')
    parser.add_argument('-p', '--port', metavar='', type=int, required=True, default=54321,
                        help='The port number of the server to be connected. Default: 54321.')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    args = parser.parse_args()
    
    client = ClientStub(args.ip, args.port)
    result = client.add(AddRequest(a=1, b=2)).sum
    print(f'1 + 2 = {result}')
    result = client.sub(SubRequest(a=1, b=2)).diff
    print(f'1 - 2 = {result}')
    