import argparse
import gzip
import socket as sk
import re

from pathlib import Path
from typing import Optional, TypedDict, Protocol
from threading import Thread


class StatusCode:
    HTTP_200_OK = "200 OK"
    HTTP_404_NOT_FOUND = "404 Not Found"
    HTTP_201_CREATED = "201 Created"


CLOSED_CONNECTION_MESSAGE = ""


BASE_DIR: Optional[Path] = None


class Request(TypedDict):
    method: str
    url: str
    version: str
    headers: dict[str, list[str]]
    body: bytes


class Response(TypedDict):
    status: str
    headers: dict[str, list[str]]
    body: bytes


class BaseEndpoint(Protocol):
    @staticmethod
    def match_url(request: Request) -> bool:
        raise NotImplementedError()

    @staticmethod
    def build_response(request: Request) -> Response:
        raise NotImplementedError()


class RootEndpoint:
    @staticmethod
    def match_url(request: Request) -> bool:
        return request["url"] == "/"

    @staticmethod
    def build_response(request: Request) -> Response:
        return {
            "status": StatusCode.HTTP_200_OK,
            "headers": {},
            "body": b"",
        }


class EchoEndpoint:
    pattern = re.compile(r"/echo/(.*)")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(EchoEndpoint.pattern.match(request["url"]))

    @staticmethod
    def build_response(request: Request) -> Response:
        echo_match = EchoEndpoint.pattern.match(request["url"])
        message = echo_match.group(1)
        encoding_names = request["headers"].get("accept-encoding")
        headers = {"Content-Type": ["text/plain"]}
        if encoding_names and "gzip" in encoding_names:
            headers["Content-Encoding"] = ["gzip"]

        return {
            "status": StatusCode.HTTP_200_OK,
            "headers": headers,
            "body": message.encode("utf-8")
        }


class UserAgentEndpoint:
    pattern = re.compile(r"/user-agent")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(UserAgentEndpoint.pattern.match(request["url"]))

    @staticmethod
    def build_response(request: Request) -> Response:
        user_agent_values = request["headers"].get("user-agent")
        if user_agent_values:
            message = user_agent_values[0]
            return {
                "status": StatusCode.HTTP_200_OK,
                "headers": {"Content-Type": ["text/plain"]},
                "body": message.encode("utf-8"),
            }
        return {
            "status": StatusCode.HTTP_404_NOT_FOUND,
            "headers": {},
            "body": b"",
        }


class FileEndpoint:
    pattern = re.compile(r"/files")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(FileEndpoint.pattern.match(request["url"]))

    @staticmethod
    def build_response(request: Request) -> Response:
        if file_name_match := re.compile(r".*/files/(.*)").match(request["url"]):
            file_name = file_name_match.group(1)
            if body := request["body"]:
                with open(BASE_DIR / file_name, "wb") as file:
                    file.write(body)
                return {
                    "status": StatusCode.HTTP_201_CREATED,
                    "headers": {},
                    "body": b"",
                }
            else:
                try:
                    with open(BASE_DIR / file_name, "rb") as file:
                        data = file.read()
                except FileNotFoundError:
                    return {
                        "status": StatusCode.HTTP_404_NOT_FOUND,
                        "headers": {},
                        "body": b"",
                    }
                else:
                    return {
                        "status": StatusCode.HTTP_200_OK,
                        "headers": {"Content-Type": ["application/octet-stream"]},
                        "body": data,
                    }
        return {
            "status": StatusCode.HTTP_404_NOT_FOUND,
            "headers": {},
            "body": b"",
        }


REGISTERED_ENDPOINTS: list[BaseEndpoint] = [
    RootEndpoint,
    EchoEndpoint,
    UserAgentEndpoint,
    FileEndpoint,
]


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
