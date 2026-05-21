from __future__ import annotations

import hashlib
import os
import re
from typing import Any

from oz_api.embedding_jobs import cache_schema_version, embedding_cache_key, execute, rows, valid_embedding
from oz_api.embeddings import embedding_dimensions, embedding_model, embedding_provider
from oz_api.observability import observe_duration
from oz_api.retrieval import vector_literal
from oz_crawler.embeddings import embeddings_for_texts
from oz_crawler.token_counting import token_count

AGENT_CARD_TABLES = {"code_examples", "api_operations", "sdk_methods", "agent_recipes"}


def ensure_agent_card_embeddings(connection: Any, version_id: int) -> dict[str, int | str]:
    if not agent_card_embeddings_enabled() or embedding_provider() == "none":
        return {"status": "skipped", "pending": 0, "cached": 0, "embedded": 0, "failed": 0}
    pending = agent_embedding_rows(connection, version_id)
    if not pending:
        return {"status": "complete", "pending": 0, "cached": 0, "embedded": 0, "failed": 0}

    cached = apply_cache_hits(connection, pending)
    pending = agent_embedding_rows(connection, version_id)
    if not pending:
        return {"status": "complete", "pending": 0, "cached": cached, "embedded": 0, "failed": 0}

    with observe_duration("oz_embedding_job_duration_seconds", {"phase": "agent_card_sync_embed"}):
        embeddings = embeddings_for_texts([str(row["content"]) for row in pending])

    embedded = 0
    failed = 0
    for row, embedding in zip(pending, embeddings, strict=False):
        if not valid_embedding(embedding):
            failed += 1
            continue
        update_agent_embedding(connection, row["table_name"], int(row["id"]), embedding)
        upsert_agent_embedding_cache(connection, row, embedding)
        embedded += 1
    return {
        "status": "complete" if failed == 0 else "partial",
        "pending": len(pending),
        "cached": cached,
        "embedded": embedded,
        "failed": failed,
    }


def agent_card_embeddings_enabled() -> bool:
    return os.environ.get("OZ_AGENT_CARD_EMBEDDINGS", "1").strip().lower() not in {"0", "false", "no", "off"}


def agent_embedding_rows(connection: Any, version_id: int) -> list[dict[str, Any]]:
    result = rows(
        connection,
        """
        select 'code_examples' as table_name,
               id,
               example_key as row_key,
               concat_ws(E'\n',
                 title,
                 description,
                 caption,
                 product,
                 language,
                 task_tags_json::text,
                 imports_json::text,
                 symbols_json::text,
                 code
               ) as content
        from code_examples
        where version_id = %s
          and (
            embedding is null
            or embedding_model is distinct from %s
            or embedding_dimensions is distinct from %s
          )
        union all
        select 'api_operations' as table_name,
               id,
               operation_key as row_key,
               concat_ws(E'\n',
                 operation_id,
                 operation_name,
                 operation_kind,
                 product,
                 http_method,
                 endpoint,
                 tags_json::text,
                 summary,
                 description,
                 required_params_json::text,
                 optional_params_json::text,
                 request_schema_json::text,
                 response_schema_json::text,
                 errors_json::text
               ) as content
        from api_operations
        where version_id = %s
          and (
            embedding is null
            or embedding_model is distinct from %s
            or embedding_dimensions is distinct from %s
          )
        union all
        select 'sdk_methods' as table_name,
               id,
               method_key as row_key,
               concat_ws(E'\n',
                 symbol_name,
                 signature,
                 sdk_class,
                 sdk_method,
                 import_path,
                 module_path,
                 product,
                 language,
                 description,
                 required_params_json::text,
                 optional_params_json::text,
                 return_type,
                 errors_json::text
               ) as content
        from sdk_methods
        where version_id = %s
          and (
            embedding is null
            or embedding_model is distinct from %s
            or embedding_dimensions is distinct from %s
          )
        union all
        select 'agent_recipes' as table_name,
               id,
               recipe_key as row_key,
               concat_ws(E'\n',
                 title,
                 task_kind,
                 product,
                 language,
                 summary,
                 coalesce(code, ''),
                 info,
                 required_env_json::text,
                 required_params_json::text
               ) as content
        from agent_recipes
        where version_id = %s
          and (
            embedding is null
            or embedding_model is distinct from %s
            or embedding_dimensions is distinct from %s
          )
        order by table_name asc, id asc
        """,
        (
            version_id,
            embedding_model(),
            embedding_dimensions(),
            version_id,
            embedding_model(),
            embedding_dimensions(),
            version_id,
            embedding_model(),
            embedding_dimensions(),
            version_id,
            embedding_model(),
            embedding_dimensions(),
        ),
    )
    output = []
    for row in result:
        content = bounded_card_content(str(row.get("content") or ""))
        content_sha = normalized_content_sha(content)
        row.update(
            {
                "content": content,
                "content_sha": content_sha,
                "chunk_sha": card_sha(str(row["table_name"]), str(row["row_key"]), content_sha),
                "input_type": agent_input_type(str(row["table_name"])),
                "token_count": token_count(content),
            }
        )
        output.append(row)
    return output


def apply_cache_hits(connection: Any, pending: list[dict[str, Any]]) -> int:
    if not pending:
        return 0
    content_shas = sorted({str(row["content_sha"]) for row in pending})
    input_types = sorted({str(row.get("input_type") or agent_input_type(str(row["table_name"]))) for row in pending})
    cached_rows = rows(
        connection,
        """
        select content_sha, input_type, embedding
        from embedding_cache
        where content_sha = any(%s::text[])
          and provider = %s
          and model = %s
          and dimensions = %s
          and input_type = any(%s::text[])
          and schema_version = %s
        """,
        (content_shas, embedding_provider(), embedding_model(), embedding_dimensions(), input_types, cache_schema_version()),
    )
    cache = {(str(row["content_sha"]), str(row["input_type"])): parse_embedding(row.get("embedding")) for row in cached_rows}
    applied = 0
    for row in pending:
        embedding = cache.get((str(row["content_sha"]), str(row.get("input_type") or agent_input_type(str(row["table_name"])))))
        if not valid_embedding(embedding):
            continue
        update_agent_embedding(connection, str(row["table_name"]), int(row["id"]), embedding)
        applied += 1
    return applied


def update_agent_embedding(connection: Any, table_name: str, row_id: int, embedding: list[float]) -> None:
    if table_name not in AGENT_CARD_TABLES:
        raise ValueError(f"unsupported agent card table: {table_name}")
    execute(
        connection,
        f"""
        update {table_name}
        set embedding = %s::vector,
            embedding_model = %s,
            embedding_dimensions = %s
        where id = %s
        """,
        (vector_literal(embedding), embedding_model(), embedding_dimensions(), row_id),
    )


def upsert_agent_embedding_cache(connection: Any, row: dict[str, Any], embedding: list[float]) -> None:
    execute(
        connection,
        """
        insert into embedding_cache (
          cache_key, provider, model, dimensions, input_type, schema_version,
          chunk_sha, content_sha, token_count, embedding
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
        on conflict (cache_key) do update
        set embedding = excluded.embedding,
            token_count = excluded.token_count,
            created_at = now()
        """,
        (
            embedding_cache_key(str(row["content_sha"]), str(row.get("input_type") or agent_input_type(str(row["table_name"])))),
            embedding_provider(),
            embedding_model(),
            embedding_dimensions(),
            str(row.get("input_type") or agent_input_type(str(row["table_name"]))),
            cache_schema_version(),
            str(row["chunk_sha"]),
            str(row["content_sha"]),
            int(row.get("token_count") or 0),
            vector_literal(embedding),
        ),
    )


def agent_input_type(table_name: str) -> str:
    if table_name not in AGENT_CARD_TABLES:
        raise ValueError(f"unsupported agent card table: {table_name}")
    return table_name


def parse_embedding(value: Any) -> list[float] | None:
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, tuple):
        return [float(item) for item in value]
    if isinstance(value, str):
        stripped = value.strip().strip("[]")
        if not stripped:
            return []
        return [float(item) for item in stripped.split(",")]
    return None


def bounded_card_content(value: str) -> str:
    return value.strip()[:12000]


def normalized_content_sha(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def card_sha(table_name: str, row_key: str, content_sha: str) -> str:
    return hashlib.sha256(f"{table_name}\0{row_key}\0{content_sha}".encode("utf-8")).hexdigest()
