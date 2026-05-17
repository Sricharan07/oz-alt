from __future__ import annotations

from functools import lru_cache

import tiktoken


@lru_cache(maxsize=1)
def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")


def token_count(text: str) -> int:
    if not text:
        return 1
    return max(1, len(_encoding().encode(text)))
