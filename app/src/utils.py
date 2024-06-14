import gzip
import re
from pathlib import Path

from app.src.schemas import Request, Response


def create_file(path: Path, content: bytes) -> None:
    with open(path, "wb") as file:
        file.write(content)


def read_file(path: Path) -> bytes | None:
    try:
        with open(path, "rb") as file:
            file_content = file.read()
    except FileNotFoundError:
        file_content = None

    return file_content


def parse_http_request(request_data: bytes) -> Request:
    request_parts = request_data.split(b"\r\n")
    (method, url, version) = request_parts[0].decode("utf-8").split()
    request = Request(
        method=method,
        url=url,
        version=version,
        body=request_parts[-1]
    )

    header_pattern = re.compile(r"(.*): (.*)")
    for row_header in request_parts[1:-1]:
        header_match = header_pattern.match(row_header.decode("utf-8"))
        if header_match:
            header_name, header_value = header_match.group(1), header_match.group(2)
            request.headers[header_name.lower()] = header_value.split(', ')

    return request


def encode_response(response: Response) -> bytes:
    encoded_version = b"HTTP/1.1"
    encoded_status = response.status.encode("utf-8")
    encoded_headers = b""

    encoded_body = response.body
    if response.headers.get("Content-Encoding") == ["gzip"]:
        encoded_body = gzip.compress(encoded_body)

    response.headers["Content-Length"] = [str(len(encoded_body))]

    for header_name, header_values in response.headers.items():
        encoded_name = header_name.encode("utf-8")
        encoded_values = (",".join(header_values)).encode("utf-8")
        encoded_headers = encoded_headers + encoded_name + b": " + encoded_values + b"\r\n"

    return encoded_version + b" " + encoded_status + b"\r\n" + encoded_headers + b"\r\n" + encoded_body
