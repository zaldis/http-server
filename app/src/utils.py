from pathlib import Path


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
