import argparse
import gzip
import socket as sk
import re
from pathlib import Path
from typing import Optional, TypedDict, Protocol

from threading import Thread


OK_MESSAGE = b"HTTP/1.1 200 OK\r\n\r\n"
CREATED_MESSAGE = b"HTTP/1.1 201 Created\r\n\r\n"
NOT_FOUND_MESSAGE = b"HTTP/1.1 404 Not Found\r\n\r\n"
ECHO_MESSAGE = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {}\r\n\r\n{}"

CLOSED_CONNECTION_MESSAGE = ""


ECHO_ENDPOINT_PATTERN = re.compile(r"/echo/(.*)")
USER_AGENT_ENDPOINT_PATTERN = re.compile(r"/user-agent")
FILE_ENDPOINT_PATTERN = re.compile(r"/files")

BASE_DIR: Optional[Path] = None


class Request(TypedDict):
    method: str
    url: str
    version: str
    headers: dict[str, list[str]]
    body: bytes


class BaseEndpoint(Protocol):
    @staticmethod
    def match_url(request: Request) -> bool:
        raise NotImplementedError()

    @staticmethod
    def handle(request: Request) -> bytes:
        raise NotImplementedError()


class RootEndpoint:
    @staticmethod
    def match_url(request: Request) -> bool:
        return request["url"] == "/"

    @staticmethod
    def handle(request: Request) -> bytes:
        return OK_MESSAGE


class EchoEndpoint(BaseEndpoint):
    pattern = re.compile(r"/echo/(.*)")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(ECHO_ENDPOINT_PATTERN.match(request["url"]))

    @staticmethod
    def handle(request: Request) -> bytes:
        echo_match = EchoEndpoint.pattern.match(request["url"])
        message = echo_match.group(1).encode("utf-8")
        encoding_names = request["headers"].get("accept-encoding")
        headers = [b"Content-Type: text/plain"]
        if encoding_names and "gzip" in encoding_names:
            headers.append(b"Content-Encoding: " + b"gzip")
            message = gzip.compress(message)

        return _build_echo_message(message, headers=headers)


class UserAgentEndpoint(BaseEndpoint):
    pattern = re.compile(r"/user-agent")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(UserAgentEndpoint.pattern.match(request["url"]))

    @staticmethod
    def handle(request: Request) -> bytes:
        user_agent_values = request["headers"].get("user-agent")
        if user_agent_values:
            message = user_agent_values[0]
            return _build_echo_message(message.encode("utf-8"), headers=[b"Content-Type: text/plain"])
        return b""


class FileEndpoint(BaseEndpoint):
    pattern = re.compile(r"/files")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(FileEndpoint.pattern.match(request["url"]))

    @staticmethod
    def handle(request: Request) -> bytes:
        if file_name_match := re.compile(r".*/files/(.*)").match(request["url"]):
            file_name = file_name_match.group(1)
            if body := request["body"]:
                with open(BASE_DIR / file_name, "wb") as file:
                    file.write(body)
                return CREATED_MESSAGE
            else:
                try:
                    with open(BASE_DIR / file_name, "rb") as file:
                        data = file.read()
                except FileNotFoundError:
                    return NOT_FOUND_MESSAGE
                else:
                    return _build_bytes_message(data)
        return b""


ENDPOINTS: list[BaseEndpoint] = [
    RootEndpoint,
    EchoEndpoint,
    UserAgentEndpoint,
    FileEndpoint,
]


def run_http_server(port: int, base_directory: Path = Path('/tmp/')) -> None:
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

        for endpoint in ENDPOINTS:
            if endpoint.match_url(request):
                client_socket.send(endpoint.handle(request))
                break
        else:
            client_socket.send(NOT_FOUND_MESSAGE)

        # if request["url"] == "/":
        #     client_socket.send(OK_MESSAGE)
        #     return

        # if echo_match := ECHO_ENDPOINT_PATTERN.match(request["url"]):
        #     message = echo_match.group(1).encode("utf-8")
        #     encoding_names = request["headers"].get("accept-encoding")
        #     headers = []
        #     if encoding_names:
        #         if "gzip" in encoding_names:
        #             headers = [b"Content-Encoding: " + b"gzip"]
        #             message = gzip.compress(message)
        #     headers.append(b"Content-Type: text/plain")
        #
        #     client_socket.send(_build_echo_message(message, headers=headers))
        #     return

        # if USER_AGENT_ENDPOINT_PATTERN.match(request["url"]):
        #     user_agent_values = request["headers"].get("user-agent")
        #     if user_agent_values:
        #         message = user_agent_values[0]
        #         client_socket.send(_build_echo_message(message.encode("utf-8"), headers=[b"Content-Type: text/plain"]))
        #         return

        # if FILE_ENDPOINT_PATTERN.match(request["url"]):
        #     if file_name_match := re.compile(r".*/files/(.*)").match(request["url"]):
        #         file_name = file_name_match.group(1)
        #         if body := request["body"]:
        #             with open(BASE_DIR / file_name, "wb") as file:
        #                 file.write(body)
        #             client_socket.send(CREATED_MESSAGE)
        #         else:
        #             try:
        #                 with open(BASE_DIR / file_name, "rb") as file:
        #                     data = file.read()
        #             except FileNotFoundError:
        #                 client_socket.send(NOT_FOUND_MESSAGE)
        #             else:
        #                 client_socket.send(_build_bytes_message(data))
        #         return

        # client_socket.send(NOT_FOUND_MESSAGE)


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


def _build_echo_message(message: bytes, headers: Optional[list[bytes]] = None) -> bytes:
    message_size = str(len(message)).encode("utf-8")

    encoded_headers = b"Content-Length: " + message_size
    if headers is not None:
        for header in headers:
            encoded_headers = encoded_headers + b"\r\n" + header

    return (
        b"HTTP/1.1 200 OK\r\n" + encoded_headers + b"\r\n\r\n" + message
    )


def _build_bytes_message(message: bytes) -> bytes:
    message_size = str(len(message)).encode("utf-8")
    return (
        b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: "
        + message_size + b"\r\n\r\n" + message
    )


def main():
    print("Logs from your program will appear here!")

    parser = argparse.ArgumentParser(
        prog="Zaldis HTTP Server",
        description="Custom HTTP Server developed by Zaldis"
    )
    parser.add_argument(
        '-d', '--directory'
    )
    args = parser.parse_args()

    global BASE_DIR
    BASE_DIR = args.directory and Path(args.directory)

    try:
        run_http_server(port=4221)
    except KeyboardInterrupt:
        print("Server shutting down...")


if __name__ == "__main__":
    main()
