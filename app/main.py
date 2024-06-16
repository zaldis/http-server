import argparse
import socket as sk

from pathlib import Path
from threading import Thread

from app.src.endpoint import REGISTERED_ENDPOINTS, HttpEndpointNotMatchError
from app.src.enums import StatusCode
from app.src.schemas import Response, Request
from app.src import settings, utils


def run_http_server(port: int) -> None:
    server_socket = sk.create_server(("localhost", port), reuse_port=True)

    while True:
        print("Waiting for connection...")
        client_socket, client_address = server_socket.accept()

        print("New connection with ", client_address)
        thread = Thread(target=handle_http_connection, args=(client_socket, ))
        thread.start()


def handle_http_connection(client_socket: sk.socket) -> None:
    with client_socket:
        http_request_line = client_socket.recv(1024)
        request = utils.parse_http_request(http_request_line)
        response = handle_http_request(request)
        http_response_line = utils.encode_response(response)
        client_socket.send(http_response_line)


def handle_http_request(request: Request) -> Response:
    for endpoint in REGISTERED_ENDPOINTS:
        try:
            response = endpoint.activate(request)
        except HttpEndpointNotMatchError:
            ...
        else:
            break
    else:
        response = Response(status=StatusCode.HTTP_404_NOT_FOUND)
    return response


def main():
    print("Logs from your program will appear here!")

    parser = argparse.ArgumentParser(
        prog="Zaldis HTTP Server",
        description="Custom HTTP Server developed by Zaldis"
    )
    parser.add_argument('-d', '--directory')
    args = parser.parse_args()

    settings.BASE_DIR = args.directory and Path(args.directory)
    try:
        run_http_server(port=4221)
    except KeyboardInterrupt:
        print("Server shutting down...")


if __name__ == "__main__":
    main()
