def read_file(file_path: str, *args, **kwargs) -> str:
    with open(file_path, "r", encoding="utf-8", *args, **kwargs) as f:
        return f.read()


def write_file(file_path: str, content: str, *args, **kwargs) -> None:
    with open(file_path, "w", encoding="utf-8", *args, **kwargs) as f:
        f.write(content)
