import socket as sk
import re

from threading import Thread


OK_MESSAGE = b"HTTP/1.1 200 OK\r\n\r\n"
NOT_FOUND_MESSAGE = b"HTTP/1.1 404 Not Found\r\n\r\n"
ECHO_MESSAGE = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {}\r\n\r\n{}"

CLOSED_CONNECTION_MESSAGE = ""


ECHO_ENDPOINT_PATTERN = re.compile(r"/echo/(.*)")
USER_AGENT_PATTERN = re.compile(r"/user-agent")


def run_http_server() -> None:
    server_socket = sk.create_server(("localhost", 4221), reuse_port=True)

    while True:
        print("Waiting for connection...")
        client_socket, client_address = server_socket.accept()

        print("New connection with ", client_address)
        thread = Thread(target=handle_http_request, args=(client_socket, ))
        thread.run()


def handle_http_request(client_socket: sk.socket) -> None:
    with client_socket:
        while True:
            data = client_socket.recv(1024).decode("utf-8")
            request_data = data.split("\r\n")
            if request_data[0] == CLOSED_CONNECTION_MESSAGE:
                break

            request_line = request_data[0]
            request_target = request_line.split(" ")[1]
            if request_target == "/":
                client_socket.send(OK_MESSAGE)
                continue

            if echo_match := ECHO_ENDPOINT_PATTERN.match(request_target):
                message = echo_match.group(1)
                client_socket.send(_build_echo_message(message))
                continue

            if USER_AGENT_PATTERN.match(request_target):
                agent_items = [row for row in request_data if 'user-agent: ' in row.lower()]
                if len(agent_items) == 1:
                    message = agent_items[0][len('user-agent: ')-1:].strip()
                    client_socket.send(_build_echo_message(message))
                    continue

            client_socket.send(NOT_FOUND_MESSAGE)


def _build_echo_message(message: str) -> bytes:
    body_size = str(len(message)).encode("utf-8")
    encoded_body = message.encode("utf-8")
    return b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + body_size + b"\r\n\r\n" + encoded_body


def main():
    print("Logs from your program will appear here!")

    try:
        run_http_server()
    except KeyboardInterrupt:
        print("Server shutting down...")


if __name__ == "__main__":
    main()
