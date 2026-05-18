from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import request
from uuid import uuid4

from oz_api.embeddings import embedding_dimensions, embedding_model, embedding_provider, voyage_api_key
from oz_api.retrieval import vector_literal
from oz_crawler.embeddings import embeddings_for_texts
from oz_crawler.token_counting import token_count

LOGGER = logging.getLogger(__name__)
DOCUMENT_INPUT_TYPE = "document"
BATCH_RUNNING_STATUSES = {"batch_submitted", "batch_running", "batch_partial"}
BATCH_DONE_STATUSES = {"completed", "partially_completed", "cancelled"}


@dataclass(frozen=True)
class EmbeddingEnsureResult:
    status: str
    mode: str
    job_id: int | None
    version_id: int | None
    total_chunks: int
    pending_chunks: int
    cached_chunks: int
    embedded_chunks: int
    failed_chunks: int = 0

    @property
    def complete(self) -> bool:
        return self.status in {"embeddings_applied", "dedupe_done", "eval_done", "promoted"}


def ensure_version_embeddings(
    connection: Any,
    version_id: int,
    *,
    crawler_job_id: int | None = None,
    force_sync: bool = False,
) -> EmbeddingEnsureResult:
    chunks = version_chunks(connection, version_id)
    enforce_library_caps(chunks)
    job_id = open_embedding_job(connection, version_id, crawler_job_id, chunks)
    active_job = embedding_job_row(connection, job_id)
    if active_job and str(active_job.get("status") or "") in {"batch_submitted", "batch_running"}:
        pending = missing_embedding_chunks(connection, version_id)
        update_crawler_embedding_status(connection, crawler_job_id, job_id, str(active_job["status"]))
        return result(
            str(active_job["status"]),
            "batch",
            job_id,
            version_id,
            chunks,
            len(pending),
            int(active_job.get("cached_chunks") or 0),
            int(active_job.get("embedded_chunks") or 0),
        )
    if active_job and str(active_job.get("status") or "") == "batch_partial":
        sync = embed_sync(
            connection,
            job_id,
            version_id,
            missing_embedding_chunks(connection, version_id),
            int(active_job.get("cached_chunks") or 0),
        )
        update_crawler_embedding_status(connection, crawler_job_id, job_id, sync.status)
        return sync
    update_embedding_job(connection, job_id, "cache_lookup")
    cache_hits = apply_cache_hits(connection, version_id, chunks)
    pending = missing_embedding_chunks(connection, version_id)
    if not pending:
        update_embedding_job(connection, job_id, "embeddings_applied", cached_chunks=cache_hits, pending_chunks=0)
        update_crawler_embedding_status(connection, crawler_job_id, job_id, "embeddings_applied")
        return result("embeddings_applied", "cache", job_id, version_id, chunks, 0, cache_hits, len(chunks))

    mode = selected_embedding_mode(len(pending), force_sync=force_sync)
    if mode == "none":
        update_embedding_job(connection, job_id, "embeddings_applied", pending_chunks=0, cached_chunks=cache_hits, embedded_chunks=0)
        update_crawler_embedding_status(connection, crawler_job_id, job_id, "embeddings_applied")
        return result("embeddings_applied", "none", job_id, version_id, chunks, 0, cache_hits, 0)
    if mode == "batch":
        batch_result = submit_voyage_batch(connection, job_id, version_id, pending, cache_hits)
        update_crawler_embedding_status(connection, crawler_job_id, job_id, batch_result.status)
        return batch_result

    sync = embed_sync(connection, job_id, version_id, pending, cache_hits)
    update_crawler_embedding_status(connection, crawler_job_id, job_id, sync.status)
    return sync


def poll_pending_embedding_jobs(connection: Any) -> list[EmbeddingEnsureResult]:
    output: list[EmbeddingEnsureResult] = []
    for job in pending_batch_jobs(connection):
        job_id = int(job["id"])
        version_id = int(job["version_id"])
        crawler_job_id = int(job["crawler_job_id"]) if job.get("crawler_job_id") is not None else None
        if batch_timed_out(job):
            mark_batch_partial(connection, job_id, "batch_timeout")
            output.append(embed_sync(connection, job_id, version_id, missing_embedding_chunks(connection, version_id), 0))
            update_crawler_embedding_status(connection, crawler_job_id, job_id, output[-1].status)
            continue
        statuses = voyage_batch_statuses(connection, job_id, batch_ids_for_job(job))
        if not statuses:
            continue
        remote_states = {str(status.get("status") or "") for status in statuses}
        if remote_states & {"validating", "in_progress", "finalizing", "cancelling"}:
            update_embedding_job(connection, job_id, "batch_running", metadata={"batches": statuses})
            continue
        if remote_states == {"cancelled"}:
            update_embedding_job(connection, job_id, "cancelled", metadata={"batches": statuses})
            update_crawler_embedding_status(connection, crawler_job_id, job_id, "cancelled")
            output.append(result("cancelled", "batch", job_id, version_id, version_chunks(connection, version_id), 0, 0, 0))
            continue
        if "failed" in remote_states:
            for status in statuses:
                if str(status.get("status") or "") in BATCH_DONE_STATUSES:
                    apply_voyage_batch_outputs(connection, job_id, version_id, status)
            mark_batch_partial(connection, job_id, "voyage_batch_failed")
            output.append(embed_sync(connection, job_id, version_id, missing_embedding_chunks(connection, version_id), 0))
            update_crawler_embedding_status(connection, crawler_job_id, job_id, output[-1].status)
            continue
        if remote_states <= BATCH_DONE_STATUSES:
            applied = sum(apply_voyage_batch_outputs(connection, job_id, version_id, status) for status in statuses)
            pending = missing_embedding_chunks(connection, version_id)
            if pending:
                mark_batch_partial(connection, job_id, f"{len(pending)} rows missing after batch")
                output.append(embed_sync(connection, job_id, version_id, pending, 0))
            else:
                update_embedding_job(connection, job_id, "embeddings_applied", embedded_chunks=applied, pending_chunks=0)
                output.append(result("embeddings_applied", "batch", job_id, version_id, version_chunks(connection, version_id), 0, 0, applied))
            update_crawler_embedding_status(connection, crawler_job_id, job_id, output[-1].status)
    return output


def cancel_embedding_job(connection: Any, embedding_job_id: int) -> None:
    row = one(
        connection,
        "select crawler_job_id, voyage_batch_id, voyage_batch_ids from embedding_jobs where id = %s",
        (embedding_job_id,),
    )
    if row:
        for batch_id in batch_ids_for_job(row):
            try:
                voyage_cancel_batch(batch_id)
            except Exception as exc:
                LOGGER.warning("failed to cancel Voyage batch %s for embedding job %s: %s", batch_id, embedding_job_id, exc)
    execute(
        connection,
        "update embedding_jobs set status = 'cancelled', updated_at = now(), completed_at = now() where id = %s",
        (embedding_job_id,),
    )
    if row and row.get("crawler_job_id") is not None:
        execute(
            connection,
            """
            update crawler_jobs
            set status = 'cancelled',
                embedding_status = 'cancelled',
                embedding_finished_at = now(),
                finished_at = coalesce(finished_at, now()),
                last_error = 'embedding job cancelled by admin'
            where id = %s
            """,
            (int(row["crawler_job_id"]),),
        )


def version_chunks(connection: Any, version_id: int) -> list[dict[str, Any]]:
    return rows(
        connection,
        """
        select id, chunk_sha, content, token_count, embedding is not null as embedded
        from chunks
        where version_id = %s
        order by id
        """,
        (version_id,),
    )


def missing_embedding_chunks(connection: Any, version_id: int) -> list[dict[str, Any]]:
    return rows(
        connection,
        """
        select id, chunk_sha, content, token_count
        from chunks
        where version_id = %s and embedding is null
        order by id
        """,
        (version_id,),
    )


def enforce_library_caps(chunks: list[dict[str, Any]]) -> None:
    max_chunks = int_env("OZ_MAX_CHUNKS_PER_LIBRARY", 25000)
    max_tokens = int_env("OZ_MAX_TOKENS_PER_LIBRARY", 10000000)
    total_tokens = sum(int(row.get("token_count") or token_count(str(row.get("content") or ""))) for row in chunks)
    if max_chunks > 0 and len(chunks) > max_chunks:
        raise RuntimeError(f"library chunk cap exceeded: {len(chunks)}/{max_chunks}")
    if max_tokens > 0 and total_tokens > max_tokens:
        raise RuntimeError(f"library token cap exceeded: {total_tokens}/{max_tokens}")


def open_embedding_job(connection: Any, version_id: int, crawler_job_id: int | None, chunks: list[dict[str, Any]]) -> int:
    existing = one(
        connection,
        """
        select id from embedding_jobs
        where version_id = %s and status in ('pending_chunks', 'cache_lookup', 'sync_embedding', 'batch_submitted', 'batch_running', 'batch_partial')
        order by created_at desc
        limit 1
        """,
        (version_id,),
    )
    if existing:
        return int(existing["id"])
    total_tokens = sum(int(row.get("token_count") or 0) for row in chunks)
    row = one(
        connection,
        """
        insert into embedding_jobs (
          crawler_job_id, version_id, status, mode, provider, model, dimensions,
          input_type, schema_version, total_chunks, pending_chunks, total_tokens
        )
        values (%s, %s, 'pending_chunks', %s, %s, %s, %s, 'document', %s, %s, %s, %s)
        returning id
        """,
        (
            crawler_job_id,
            version_id,
            selected_embedding_mode(0, force_sync=False),
            embedding_provider(),
            embedding_model(),
            embedding_dimensions(),
            cache_schema_version(),
            len(chunks),
            len([row for row in chunks if not row.get("embedded")]),
            total_tokens,
        ),
    )
    if not row:
        raise RuntimeError("embedding job was not created")
    return int(row["id"])


def apply_cache_hits(connection: Any, version_id: int, chunks: list[dict[str, Any]]) -> int:
    missing = [row for row in chunks if not row.get("embedded")]
    if not missing:
        return 0
    cache_keys = [embedding_cache_key(str(row["chunk_sha"])) for row in missing]
    cache_rows = rows(
        connection,
        "select cache_key, embedding, model, dimensions from embedding_cache where cache_key = any(%s)",
        (cache_keys,),
    )
    by_key = {str(row["cache_key"]): row for row in cache_rows}
    hits = 0
    for row in missing:
        cache = by_key.get(embedding_cache_key(str(row["chunk_sha"])))
        if not cache:
            continue
        execute(
            connection,
            """
            update chunks
            set embedding = %s::vector, embedding_model = %s, embedding_dimensions = %s
            where version_id = %s and id = %s and embedding is null
            """,
            (str(cache["embedding"]), cache["model"], int(cache["dimensions"]), version_id, int(row["id"])),
        )
        hits += 1
    return hits


def embed_sync(
    connection: Any,
    job_id: int,
    version_id: int,
    pending: list[dict[str, Any]],
    cache_hits: int,
) -> EmbeddingEnsureResult:
    update_embedding_job(connection, job_id, "sync_embedding", pending_chunks=len(pending), cached_chunks=cache_hits)
    texts = [str(row.get("content") or "") for row in pending]
    embeddings = embeddings_for_texts(texts)
    embedded = 0
    failed = 0
    for row, embedding in zip(pending, embeddings, strict=False):
        if not valid_embedding(embedding):
            failed += 1
            upsert_embedding_item(connection, job_id, row, "failed", "missing embedding")
            continue
        apply_embedding(connection, version_id, row, embedding)
        upsert_embedding_cache(connection, row, embedding)
        upsert_embedding_item(connection, job_id, row, "embedded", None)
        embedded += 1
    status = "embeddings_applied" if failed == 0 else "failed"
    update_embedding_job(
        connection,
        job_id,
        status,
        pending_chunks=max(len(pending) - embedded, 0),
        cached_chunks=cache_hits,
        embedded_chunks=embedded,
        failed_chunks=failed,
        error=None if failed == 0 else f"{failed} chunks failed to embed",
    )
    return result(status, "sync", job_id, version_id, version_chunks(connection, version_id), max(len(pending) - embedded, 0), cache_hits, embedded, failed)


def submit_voyage_batch(
    connection: Any,
    job_id: int,
    version_id: int,
    pending: list[dict[str, Any]],
    cache_hits: int,
) -> EmbeddingEnsureResult:
    api_key = voyage_api_key()
    if not api_key:
        return embed_sync(connection, job_id, version_id, pending, cache_hits)
    batch_ids: list[str] = []
    input_file_ids: list[str] = []
    batch_objects: list[dict[str, Any]] = []
    for batch_rows in split_batch_rows(pending):
        body = batch_jsonl(batch_rows)
        input_file_id = voyage_upload_file(api_key, body)
        batch = voyage_create_batch(api_key, input_file_id, version_id=version_id, job_id=job_id)
        batch_id = str(batch.get("id") or "")
        if not batch_id:
            raise RuntimeError("Voyage batch response did not include id")
        batch_ids.append(batch_id)
        input_file_ids.append(input_file_id)
        batch_objects.append(batch)
    for row in pending:
        upsert_embedding_item(connection, job_id, row, "pending", None)
    execute(
        connection,
        """
        update embedding_jobs
        set status = 'batch_running',
            mode = 'batch',
            voyage_batch_id = %s,
            voyage_batch_ids = %s::jsonb,
            voyage_input_file_id = %s,
            pending_chunks = %s,
            cached_chunks = %s,
            submitted_at = now(),
            updated_at = now(),
            metadata_json = %s::jsonb
        where id = %s
        """,
        (
            batch_ids[0],
            json.dumps(batch_ids),
            ",".join(input_file_ids),
            len(pending),
            cache_hits,
            json.dumps({"batches": batch_objects}, sort_keys=True),
            job_id,
        ),
    )
    return result("batch_running", "batch", job_id, version_id, version_chunks(connection, version_id), len(pending), cache_hits, 0)


def split_batch_rows(rows_to_embed: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    max_inputs = int_env("OZ_VOYAGE_BATCH_MAX_INPUTS", 100000)
    max_bytes = int_env("OZ_VOYAGE_BATCH_MAX_BYTES", 1000000000)
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_bytes = 0
    for row in rows_to_embed:
        line_size = len(json.dumps(batch_line(row), ensure_ascii=False).encode("utf-8")) + 1
        if current and (len(current) >= max_inputs or current_bytes + line_size > max_bytes):
            batches.append(current)
            current = []
            current_bytes = 0
        current.append(row)
        current_bytes += line_size
    if current:
        batches.append(current)
    return batches


def batch_jsonl(rows_to_embed: list[dict[str, Any]]) -> bytes:
    return b"".join(json.dumps(batch_line(row), ensure_ascii=False).encode("utf-8") + b"\n" for row in rows_to_embed)


def batch_line(row: dict[str, Any]) -> dict[str, Any]:
    return {"custom_id": str(row["chunk_sha"]), "body": {"input": [str(row.get("content") or "")]}}


def voyage_upload_file(api_key: str, body: bytes) -> str:
    boundary = f"----oz-voyage-{uuid4().hex}"
    payload = multipart_body(boundary, body)
    req = request.Request(
        "https://api.voyageai.com/v1/files",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    file_id = str(data.get("id") or "")
    if not file_id:
        raise RuntimeError("Voyage file upload response did not include id")
    return file_id


def multipart_body(boundary: str, file_body: bytes) -> bytes:
    head = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="purpose"\r\n\r\n'
        "batch\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="oz-embeddings.jsonl"\r\n'
        "Content-Type: application/jsonl\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + file_body + tail


def voyage_create_batch(api_key: str, input_file_id: str, *, version_id: int, job_id: int) -> dict[str, Any]:
    payload = {
        "endpoint": "/v1/embeddings",
        "completion_window": os.environ.get("OZ_VOYAGE_BATCH_COMPLETION_WINDOW", "12h"),
        "request_params": {
            "model": embedding_model(),
            "input_type": "document",
            "output_dimension": embedding_dimensions(),
            "output_dtype": "float",
        },
        "input_file_id": input_file_id,
        "metadata": {"version_id": str(version_id), "embedding_job_id": str(job_id), "product": "oz"},
    }
    return voyage_json_request("https://api.voyageai.com/v1/batches", api_key, payload, method="POST")


def voyage_get_batch(batch_id: str) -> dict[str, Any] | None:
    api_key = voyage_api_key()
    if not api_key or not batch_id:
        return None
    return voyage_json_request(
        f"https://api.voyageai.com/v1/batches/{batch_id}",
        api_key,
        None,
        method="GET",
        timeout=float_env("OZ_VOYAGE_STATUS_TIMEOUT_SECONDS", 3.0),
    )


def voyage_batch_statuses(connection: Any, job_id: int, batch_ids: list[str]) -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    for batch_id in batch_ids:
        try:
            status = voyage_get_batch(batch_id)
        except Exception as exc:
            LOGGER.warning("failed to poll Voyage batch %s for embedding job %s: %s", batch_id, job_id, exc)
            update_embedding_job(
                connection,
                job_id,
                "batch_running",
                metadata={"last_status_poll_error": str(exc), "last_status_poll_batch_id": batch_id},
            )
            continue
        if status:
            statuses.append(status)
    return statuses


def batch_ids_for_job(job: dict[str, Any]) -> list[str]:
    raw = job.get("voyage_batch_ids")
    if isinstance(raw, list):
        ids = [str(item) for item in raw if str(item).strip()]
    elif isinstance(raw, str) and raw.strip().startswith("["):
        try:
            ids = [str(item) for item in json.loads(raw) if str(item).strip()]
        except json.JSONDecodeError:
            ids = []
    else:
        ids = []
    fallback = str(job.get("voyage_batch_id") or "").strip()
    if fallback and fallback not in ids:
        ids.insert(0, fallback)
    return ids


def voyage_cancel_batch(batch_id: str) -> None:
    api_key = voyage_api_key()
    if api_key and batch_id:
        voyage_json_request(f"https://api.voyageai.com/v1/batches/{batch_id}/cancel", api_key, None, method="POST")


def voyage_json_request(
    url: str,
    api_key: str,
    payload: dict[str, Any] | None,
    *,
    method: str,
    timeout: float = 60.0,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(
        url,
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method=method,
    )
    with request.urlopen(req, timeout=timeout) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    return parsed if isinstance(parsed, dict) else {}


def apply_voyage_batch_outputs(connection: Any, job_id: int, version_id: int, batch: dict[str, Any]) -> int:
    output_file_id = str(batch.get("output_file_id") or "")
    if not output_file_id:
        return 0
    content = voyage_file_content(output_file_id)
    applied = 0
    by_sha = {str(row["chunk_sha"]): row for row in missing_embedding_chunks(connection, version_id)}
    for line in content.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        chunk_sha = str(item.get("custom_id") or "")
        row = by_sha.get(chunk_sha)
        embedding = batch_line_embedding(item)
        if not row or not valid_embedding(embedding):
            continue
        apply_embedding(connection, version_id, row, embedding)
        upsert_embedding_cache(connection, row, embedding)
        upsert_embedding_item(connection, job_id, row, "embedded", None)
        applied += 1
    error_file_id = str(batch.get("error_file_id") or "")
    execute(
        connection,
        """
        update embedding_jobs
        set voyage_output_file_id = %s,
            voyage_error_file_id = %s,
            embedded_chunks = embedded_chunks + %s,
            updated_at = now(),
            metadata_json = %s::jsonb
        where id = %s
        """,
        (output_file_id, error_file_id or None, applied, json.dumps(batch, sort_keys=True), job_id),
    )
    return applied


def voyage_file_content(file_id: str) -> str:
    api_key = voyage_api_key()
    if not api_key:
        return ""
    req = request.Request(
        f"https://api.voyageai.com/v1/files/{file_id}/content",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    with request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8")


def batch_line_embedding(item: dict[str, Any]) -> list[float] | None:
    response_body = ((item.get("response") or {}).get("body") or {}) if isinstance(item.get("response"), dict) else {}
    data = response_body.get("data") if isinstance(response_body, dict) else None
    if not isinstance(data, list) or not data:
        return None
    embedding = data[0].get("embedding") if isinstance(data[0], dict) else None
    return [float(value) for value in embedding] if isinstance(embedding, list) else None


def apply_embedding(connection: Any, version_id: int, row: dict[str, Any], embedding: list[float]) -> None:
    execute(
        connection,
        """
        update chunks
        set embedding = %s::vector,
            embedding_model = %s,
            embedding_dimensions = %s
        where version_id = %s and id = %s
        """,
        (vector_literal(embedding), embedding_model(), embedding_dimensions(), version_id, int(row["id"])),
    )


def upsert_embedding_cache(connection: Any, row: dict[str, Any], embedding: list[float]) -> None:
    execute(
        connection,
        """
        insert into embedding_cache (
          cache_key, provider, model, dimensions, input_type, schema_version,
          chunk_sha, token_count, embedding
        )
        values (%s, %s, %s, %s, 'document', %s, %s, %s, %s::vector)
        on conflict (cache_key) do update
        set embedding = excluded.embedding,
            token_count = excluded.token_count,
            created_at = now()
        """,
        (
            embedding_cache_key(str(row["chunk_sha"])),
            embedding_provider(),
            embedding_model(),
            embedding_dimensions(),
            cache_schema_version(),
            str(row["chunk_sha"]),
            int(row.get("token_count") or 0),
            vector_literal(embedding),
        ),
    )


def upsert_embedding_item(connection: Any, job_id: int, row: dict[str, Any], status: str, error: str | None) -> None:
    execute(
        connection,
        """
        insert into embedding_job_items (embedding_job_id, chunk_id, chunk_sha, cache_key, status, error)
        values (%s, %s, %s, %s, %s, %s)
        on conflict (embedding_job_id, chunk_id) do update
        set status = excluded.status,
            error = excluded.error,
            updated_at = now()
        """,
        (job_id, int(row["id"]), str(row["chunk_sha"]), embedding_cache_key(str(row["chunk_sha"])), status, error),
    )


def update_embedding_job(connection: Any, job_id: int, status: str, **fields: Any) -> None:
    assignments = ["status = %s", "updated_at = now()"]
    params: list[Any] = [status]
    for name in ("pending_chunks", "cached_chunks", "embedded_chunks", "failed_chunks", "error"):
        if name in fields:
            assignments.append(f"{name} = %s")
            params.append(fields[name])
    if "metadata" in fields:
        assignments.append("metadata_json = %s::jsonb")
        params.append(json.dumps(fields["metadata"], sort_keys=True))
    if status in {"embeddings_applied", "failed", "cancelled"}:
        assignments.append("completed_at = now()")
    params.append(job_id)
    execute(connection, f"update embedding_jobs set {', '.join(assignments)} where id = %s", tuple(params))


def update_crawler_embedding_status(connection: Any, crawler_job_id: int | None, embedding_job_id: int | None, status: str) -> None:
    if crawler_job_id is None:
        return
    execute(
        connection,
        """
        update crawler_jobs
        set embedding_status = %s,
            embedding_job_id = %s,
            embedding_started_at = coalesce(embedding_started_at, now()),
            embedding_finished_at = case when %s in ('embeddings_applied', 'failed', 'cancelled') then now() else embedding_finished_at end,
            embedding_error = case when %s = 'failed' then coalesce(embedding_error, 'embedding job failed') else embedding_error end
        where id = %s
        """,
        (status, embedding_job_id, status, status, crawler_job_id),
    )


def pending_batch_jobs(connection: Any) -> list[dict[str, Any]]:
    limit = int_env("OZ_EMBEDDING_BATCH_POLL_LIMIT", 1)
    return rows(
        connection,
        """
        select *
        from embedding_jobs
        where status in ('batch_submitted', 'batch_running', 'batch_partial')
        order by updated_at asc
        limit %s
        """,
        (limit,),
    )


def embedding_job_row(connection: Any, embedding_job_id: int) -> dict[str, Any] | None:
    return one(connection, "select * from embedding_jobs where id = %s", (embedding_job_id,))


def batch_timed_out(job: dict[str, Any]) -> bool:
    submitted = job.get("submitted_at") or job.get("updated_at") or job.get("created_at")
    if submitted is None:
        return False
    if isinstance(submitted, str):
        try:
            submitted_dt = datetime.fromisoformat(submitted.replace("Z", "+00:00"))
        except ValueError:
            return False
    else:
        submitted_dt = submitted
    if submitted_dt.tzinfo is None:
        submitted_dt = submitted_dt.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - submitted_dt.astimezone(timezone.utc)).total_seconds() / 3600
    return age_hours > float_env("OZ_EMBEDDING_BATCH_TIMEOUT_HOURS", 18.0)


def mark_batch_partial(connection: Any, job_id: int, reason: str) -> None:
    update_embedding_job(connection, job_id, "batch_partial", error=reason)


def selected_embedding_mode(pending_count: int, *, force_sync: bool) -> str:
    configured = os.environ.get("OZ_EMBEDDING_INDEX_MODE", "auto").strip().lower()
    if force_sync or configured == "sync":
        return "sync"
    if configured == "batch":
        return "batch"
    if configured == "none" or embedding_provider() == "none":
        return "none"
    threshold = int_env("OZ_EMBEDDING_SYNC_THRESHOLD", 500)
    return "batch" if embedding_provider() == "voyage" and pending_count >= threshold else "sync"


def result(
    status: str,
    mode: str,
    job_id: int | None,
    version_id: int | None,
    chunks: list[dict[str, Any]],
    pending: int,
    cached: int,
    embedded: int,
    failed: int = 0,
) -> EmbeddingEnsureResult:
    return EmbeddingEnsureResult(status, mode, job_id, version_id, len(chunks), pending, cached, embedded, failed)


def embedding_cache_key(chunk_sha: str) -> str:
    payload = "\0".join(
        [
            cache_schema_version(),
            embedding_provider(),
            embedding_model(),
            str(embedding_dimensions()),
            DOCUMENT_INPUT_TYPE,
            chunk_sha,
        ]
    )
    import hashlib

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cache_schema_version() -> str:
    return os.environ.get("OZ_EMBEDDING_CACHE_SCHEMA_VERSION", "v1").strip() or "v1"


def valid_embedding(value: Any) -> bool:
    return isinstance(value, list) and len(value) == embedding_dimensions() and all(isinstance(item, (int, float)) for item in value)


def one(connection: Any, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    result_rows = rows(connection, sql, params)
    return result_rows[0] if result_rows else None


def rows(connection: Any, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        if cursor.description is None:
            return []
        columns = [getattr(column, "name", column[0]) for column in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


def execute(connection: Any, sql: str, params: tuple[Any, ...]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        LOGGER.warning("invalid %s=%r", name, os.environ.get(name))
        return default


def float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        LOGGER.warning("invalid %s=%r", name, os.environ.get(name))
        return default
