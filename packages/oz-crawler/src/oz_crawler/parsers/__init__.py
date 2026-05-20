from __future__ import annotations

from oz_crawler.parsers.asyncapi import asyncapi_chunks
from oz_crawler.parsers.openapi import openapi_chunks
from oz_crawler.parsers.type_defs import type_definition_chunks

__all__ = ["asyncapi_chunks", "openapi_chunks", "type_definition_chunks"]
