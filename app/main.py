import argparse
import gzip
import socket as sk
import re

from pathlib import Path
from threading import Thread

from app.src.endpoint import REGISTERED_ENDPOINTS
from app.src.enums import StatusCode
from app.src.schemas import Request, Response
from app.src import settings


def run_http_server(port: int) -> None:
    server_socket = sk.create_server(("localhost", port), reuse_port=True)

    while True:
        print("Waiting for connection...")
        client_socket, client_address = server_socket.accept()

        print("New connection with ", client_address)
        thread = Thread(target=handle_http_request, args=(client_socket, ))
        thread.start()


def handle_http_request(client_socket: sk.socket) -> None:
    with client_socket:
        data = client_socket.recv(1024)
        request = _parse_http_request(data)

        for endpoint in REGISTERED_ENDPOINTS:
            if endpoint.match_url(request):
                response = endpoint.build_response(request)
                break
        else:
            response = {
                "status": StatusCode.HTTP_404_NOT_FOUND,
                "headers": {},
                "body": b""
            }

        encoded_response = _encode_response(response)
        client_socket.send(encoded_response)


def _parse_http_request(request_data: bytes) -> Request:
    request: Request = {
        "method": "",
        "url": "",
        "version": "",
        "headers": {},
        "body": b"",
    }
    request_parts = request_data.split(b"\r\n")
    (request["method"], request["url"], request["version"]) = request_parts[0].decode("utf-8").split()
    request["body"] = request_parts[-1]

    header_pattern = re.compile(r"(.*): (.*)")
    for row_header in request_parts[1:-1]:
        header_match = header_pattern.match(row_header.decode("utf-8"))
        if header_match:
            header_name, header_value = header_match.group(1), header_match.group(2)
            request["headers"][header_name.lower()] = header_value.split(', ')

    return request


def _encode_response(response: Response) -> bytes:
    encoded_version = b"HTTP/1.1"
    encoded_status = response["status"].encode("utf-8")
    encoded_headers = b""

    encoded_body = response["body"]
    if response["headers"].get("Content-Encoding") == ["gzip"]:
        encoded_body = gzip.compress(encoded_body)

    response["headers"]["Content-Length"] = [str(len(encoded_body))]

    for key, values in response["headers"].items():
        encoded_headers = encoded_headers + key.encode("utf-8") + b": " + (",".join(values)).encode("utf-8") + b"\r\n"

    return encoded_version + b" " + encoded_status + b"\r\n" + encoded_headers + b"\r\n" + encoded_body


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
