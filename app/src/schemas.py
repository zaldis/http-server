from typing import TypedDict


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
