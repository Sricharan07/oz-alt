from __future__ import annotations

import re
from functools import lru_cache

try:
    import tiktoken
except ImportError:  # pragma: no cover - dependency is installed in production images
    tiktoken = None  # type: ignore[assignment]


@lru_cache(maxsize=1)
def _encoding():
    if tiktoken is None:
        return None
    return tiktoken.get_encoding("cl100k_base")


def token_count(text: str) -> int:
    if not text:
        return 0
    encoding = _encoding()
    if encoding is None:
        return max(1, len(re.findall(r"\w+|[^\w\s]", text)))
    return max(1, len(encoding.encode(text)))
