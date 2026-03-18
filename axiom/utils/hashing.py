import hashlib


def hash_source(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()
