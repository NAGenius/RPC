from clientstub import ClientStub
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RPC Client', add_help=False)
    # required
    parser.add_argument('-i', '--ip', metavar='', type=str, required=False, default='127.0.0.1',
                        help='The IP address of the server to be connected.')
    parser.add_argument('-p', '--port', metavar='', type=int, required=False, default=54321,
                        help='The port number of the server to be connected.')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit.')
    args = parser.parse_args()
    
    client = ClientStub(args.ip, args.port)
    result = client.add(1, 2)
    print(f'1 + 2 = {result}')
    