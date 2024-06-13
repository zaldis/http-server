from dataclasses import dataclass, field
from typing import TypedDict


@dataclass
class Request:
    method: str
    url: str
    version: str
    headers: dict[str, list[str]] = field(default_factory=dict)
    body: bytes = b""


@dataclass
class Response:
    status: str
    headers: dict[str, list[str]] = field(default_factory=dict)
    body: bytes = b""
