import re
from typing import Protocol

from .enums import StatusCode
from .schemas import Request, Response
from . import settings


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
        return request.url == "/"

    @staticmethod
    def build_response(request: Request) -> Response:
        return Response(
            status=StatusCode.HTTP_200_OK
        )


class EchoEndpoint:
    pattern = re.compile(r"/echo/(.*)")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(EchoEndpoint.pattern.match(request.url))

    @staticmethod
    def build_response(request: Request) -> Response:
        echo_match = EchoEndpoint.pattern.match(request.url)
        message = echo_match.group(1)
        encoding_names = request.headers.get("accept-encoding")
        headers = {"Content-Type": ["text/plain"]}
        if encoding_names and "gzip" in encoding_names:
            headers["Content-Encoding"] = ["gzip"]

        return Response(
            status=StatusCode.HTTP_200_OK,
            headers=headers,
            body=message.encode("utf-8")
        )


class UserAgentEndpoint:
    pattern = re.compile(r"/user-agent")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(UserAgentEndpoint.pattern.match(request.url))

    @staticmethod
    def build_response(request: Request) -> Response:
        user_agent_values = request.headers.get("user-agent")
        if user_agent_values:
            message = user_agent_values[0]
            return Response(
                status=StatusCode.HTTP_200_OK,
                headers={"Content-Type": ["text/plain"]},
                body=message.encode("utf-8"),
            )
        return Response(status=StatusCode.HTTP_404_NOT_FOUND)


class FileEndpoint:
    pattern = re.compile(r"/files")

    @staticmethod
    def match_url(request: Request) -> bool:
        return bool(FileEndpoint.pattern.match(request.url))

    @staticmethod
    def build_response(request: Request) -> Response:
        if file_name_match := re.compile(r".*/files/(.*)").match(request.url):
            file_name = file_name_match.group(1)
            if body := request.body:
                with open(settings.BASE_DIR / file_name, "wb") as file:
                    file.write(body)
                return Response(status=StatusCode.HTTP_201_CREATED)
            else:
                try:
                    with open(settings.BASE_DIR / file_name, "rb") as file:
                        data = file.read()
                except FileNotFoundError:
                    return Response(status=StatusCode.HTTP_404_NOT_FOUND)
                else:
                    return Response(
                        status=StatusCode.HTTP_200_OK,
                        headers={"Content-Type": ["application/octet-stream"]},
                        body=data,
                    )
        return Response(status=StatusCode.HTTP_404_NOT_FOUND)


REGISTERED_ENDPOINTS: list[BaseEndpoint] = [
    RootEndpoint,
    EchoEndpoint,
    UserAgentEndpoint,
    FileEndpoint,
]
