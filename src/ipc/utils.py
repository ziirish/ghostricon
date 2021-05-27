def to_bytes(src: str) -> bytes:
    return src.encode("utf-8")


def to_str(src: bytes) -> str:
    return src.decode("utf-8")
