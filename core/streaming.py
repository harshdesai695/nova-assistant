from typing import Generator, Iterable


def chunk_text(text: str, chunk_size: int = 24) -> Generator[str, None, None]:
    if not text:
        return
    words = text.split()
    if not words:
        return
    buf = []
    size = 0
    for w in words:
        buf.append(w)
        size += len(w) + 1
        if size >= chunk_size:
            yield " ".join(buf)
            buf = []
            size = 0
    if buf:
        yield " ".join(buf)


def stream_from_final_text(text: str) -> list[str]:
    return list(chunk_text(text))
