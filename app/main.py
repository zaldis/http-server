import socket as sk

OK_MESSAGE = b"HTTP/1.1 200 OK\r\n\r\n"
NOT_FOUND_MESSAGE = b"HTTP/1.1 404 Not Found\r\n\r\n"

CLOSED_CONNECTION_MESSAGE = ""


def run_http_server() -> None:
    server_socket = sk.create_server(("localhost", 4221), reuse_port=True)

    while True:
        print("Waiting for connection...")
        client_socket, client_address = server_socket.accept()

        print("New connection with ", client_address)
        handle_http_request(client_socket)


def handle_http_request(client_socket: sk.socket) -> None:
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            request_data = data.decode().split("\r\n")
            if request_data[0] == CLOSED_CONNECTION_MESSAGE:
                break
            request_line = request_data[0]
            request_target = request_line.split(" ")[1]
            message = OK_MESSAGE if request_target == '/' else NOT_FOUND_MESSAGE
            client_socket.send(message)


def main():
    print("Logs from your program will appear here!")

    try:
        run_http_server()
    except KeyboardInterrupt:
        print("Server shutting down...")


if __name__ == "__main__":
    main()
