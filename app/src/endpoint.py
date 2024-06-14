import re
from typing import Protocol

from .enums import StatusCode
from .schemas import Request, Response
from . import settings
from .utils import create_file, read_file


class HttpEndpointNotMatchError(Exception):
    pass


class EndpointProtocol(Protocol):
    def activate(self, request: Request) -> Response:
        ...


class BaseEndpoint:
    pattern: re.Pattern[str]
    _args: tuple[str, ...]

    def activate(self, request: Request) -> Response:
        self._feed_url(request.url)
        return self.handle_request(request)

    def handle_request(self, request: Request) -> Response:
        raise NotImplementedError

    def _feed_url(self, url: str):
        endpoint_match = self.pattern.match(url)
        if not endpoint_match:
            raise HttpEndpointNotMatchError()
        self.args = endpoint_match.groups()


class RootEndpoint(BaseEndpoint):
    pattern = re.compile("^/$")

    def handle_request(self, request: Request) -> Response:
        return Response(
            status=StatusCode.HTTP_200_OK
        )


class EchoEndpoint(BaseEndpoint):
    pattern = re.compile(r"/echo/(.*)")

    def handle_request(self, request: Request) -> Response:
        message = self.args[0]
        encoding_names = request.headers.get("accept-encoding")
        headers = {"Content-Type": ["text/plain"]}
        if encoding_names and "gzip" in encoding_names:
            headers["Content-Encoding"] = ["gzip"]

        return Response(
            status=StatusCode.HTTP_200_OK,
            headers=headers,
            body=message.encode("utf-8")
        )


class UserAgentEndpoint(BaseEndpoint):
    pattern = re.compile(r"/user-agent")

    def handle_request(self, request: Request) -> Response:
        user_agent_values = request.headers.get("user-agent")
        if user_agent_values:
            message = user_agent_values[0]
            return Response(
                status=StatusCode.HTTP_200_OK,
                headers={"Content-Type": ["text/plain"]},
                body=message.encode("utf-8"),
            )
        return Response(status=StatusCode.HTTP_404_NOT_FOUND)


class FileEndpoint(BaseEndpoint):
    pattern = re.compile(r".*/files/(.*)")

    def handle_request(self, request: Request) -> Response:
        file_name = self.args[0]
        if body := request.body:
            create_file(path=settings.BASE_DIR / file_name, content=body)
            return Response(status=StatusCode.HTTP_201_CREATED)
        else:
            file_content = read_file(settings.BASE_DIR / file_name)
            if file_content is None:
                return Response(status=StatusCode.HTTP_404_NOT_FOUND)
            return Response(
                status=StatusCode.HTTP_200_OK,
                headers={"Content-Type": ["application/octet-stream"]},
                body=file_content,
            )


REGISTERED_ENDPOINTS: list[EndpointProtocol] = [
    RootEndpoint(),
    EchoEndpoint(),
    UserAgentEndpoint(),
    FileEndpoint(),
]
