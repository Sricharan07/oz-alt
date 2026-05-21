from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oz_api.agent_embeddings import ensure_agent_card_embeddings
from oz_api.indexer_artifacts import *  # noqa: F403
from oz_api.recipe_compiler import build_agent_recipes_from_surfaces, validate_agent_recipes
from oz_crawler.token_counting import token_count


class SurfaceIndexMixin:
    def rebuild_surface_dedupe_clusters(self, version_id: int) -> None:
        specs = [
            ("code_examples", "code", "coalesce(sd.source_priority, 50)", "quality_score", "confidence", "left join source_documents sd on sd.id = t.source_document_id"),
            (
                "api_operations",
                "concat_ws(' ', http_method, endpoint, operation_id, operation_name, summary, description, required_params_json::text, optional_params_json::text)",
                "coalesce(sd.source_priority, 50)",
                "quality_score",
                "confidence",
                "left join source_documents sd on sd.id = t.source_document_id",
            ),
            (
                "sdk_methods",
                "concat_ws(' ', symbol_name, sdk_class, sdk_method, signature, description, required_params_json::text, optional_params_json::text)",
                "coalesce(sd.source_priority, 50)",
                "quality_score",
                "confidence",
                "left join source_documents sd on sd.id = t.source_document_id",
            ),
            (
                "agent_recipes",
                "concat_ws(' ', title, task_kind, summary, code, info, required_params_json::text, required_env_json::text)",
                "50",
                "quality_score",
                "confidence",
                "",
            ),
        ]
        for table_name, text_expr, priority_expr, quality_expr, confidence_expr, join_sql in specs:
            self.execute(
                f"""
                update {table_name}
                   set dedupe_cluster_id = null,
                       dedupe_canonical = true
                 where version_id = %s
                """,
                (version_id,),
            )
            self.execute(
                """
                delete from dedupe_clusters
                 where version_id = %s
                   and surface_table = %s
                """,
                (version_id, table_name),
            )
            self.execute(
                f"""
                with rows as (
                  select t.id,
                         'surface:' || %s || ':' || md5(regexp_replace(lower(coalesce({text_expr}, '')), '\\s+', ' ', 'g')) as cluster_key,
                         {priority_expr} as source_priority,
                         t.{quality_expr} as quality_score,
                         t.{confidence_expr} as confidence
                  from {table_name} t
                  {join_sql}
                  where t.version_id = %s
                    and nullif(regexp_replace(coalesce({text_expr}, ''), '\\s+', '', 'g'), '') is not null
                ),
                grouped as (
                  select cluster_key,
                         array_agg(id order by source_priority asc, confidence desc, quality_score desc, id asc) as ids,
                         count(*) as member_count
                  from rows
                  group by cluster_key
                  having count(*) > 1
                ),
                inserted as (
                  insert into dedupe_clusters(
                    version_id, cluster_key, surface_table, canonical_row_id,
                    member_ids_json, member_count, method
                  )
                  select %s, cluster_key, %s, ids[1], to_jsonb(ids), member_count, 'surface_normalized_exact'
                  from grouped
                  on conflict (version_id, cluster_key) do update
                    set surface_table = excluded.surface_table,
                        canonical_row_id = excluded.canonical_row_id,
                        member_ids_json = excluded.member_ids_json,
                        member_count = excluded.member_count,
                        method = excluded.method
                  returning id, canonical_row_id, cluster_key
                )
                update {table_name} t
                   set dedupe_cluster_id = inserted.id,
                       dedupe_canonical = t.id = inserted.canonical_row_id
                  from inserted
                 where t.version_id = %s
                   and 'surface:' || %s || ':' || md5(regexp_replace(lower(coalesce({text_expr}, '')), '\\s+', ' ', 'g')) = inserted.cluster_key
                """,
                (table_name, version_id, version_id, table_name, version_id, table_name),
            )

    def rebuild_agent_surfaces(self, version_id: int, *, fixture: Path, embed_agent_cards: bool = False) -> None:
        source_ids = self.source_document_id_map(version_id)
        rows = self.context_chunk_rows(version_id)
        sections = source_section_rows(fixture)
        section_ids = self.replace_source_sections(version_id, sections, source_ids)
        self.resolve_chunk_sections(version_id, section_ids)
        examples = code_example_rows(fixture)
        operations = api_operation_rows(fixture)
        methods = sdk_method_rows(fixture)
        example_ids = self.replace_code_examples(version_id, examples, source_ids, section_ids)
        operation_ids = self.replace_api_operations(version_id, operations, source_ids, section_ids)
        method_ids = self.replace_sdk_methods(version_id, methods, source_ids, section_ids)
        recipes = build_agent_recipes_from_surfaces(
            code_examples=examples,
            api_operations=operations,
            sdk_methods=methods,
            source_sections=sections,
            code_example_ids=example_ids,
            api_operation_ids=operation_ids,
            sdk_method_ids=method_ids,
            source_section_ids=section_ids,
        )
        validate_agent_recipes(
            recipes,
            code_example_ids=example_ids,
            api_operation_ids=operation_ids,
            sdk_method_ids=method_ids,
            source_section_ids=section_ids,
        )
        self.replace_agent_recipes(version_id, recipes)
        self.rebuild_surface_dedupe_clusters(version_id)
        if embed_agent_cards:
            ensure_agent_card_embeddings(self.connection, version_id)

    def source_document_id_map(self, version_id: int) -> dict[str, int]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "select source_document_key, id from source_documents where version_id = %s",
                (version_id,),
            )
            rows = cursor.fetchall()
        return {str(row[0]): int(row[1]) for row in rows}

    def context_chunk_rows(self, version_id: int) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select c.id, c.source_document_id, c.path, c.start_line, c.end_line, c.source_url,
                       c.ordinal, c.chunk_key, c.parent_chunk_key, c.chunk_sha, c.content_sha,
                       c.heading_path, c.symbols, c.content_type, c.quality_score, c.token_count,
                       c.source_anchor, c.content, c.dedupe_canonical,
                       coalesce(sd.title, '') as source_title,
                       coalesce(sd.source_type, '') as source_type,
                       coalesce(sd.document_role, '') as document_role,
                       coalesce(sd.product, '') as product,
                       coalesce(sd.product_confidence, 0) as product_confidence,
                       coalesce(sd.language, '') as source_language,
                       coalesce(sd.source_priority, 50) as source_priority,
                       coalesce(c.metadata_json, '{}'::jsonb) as chunk_metadata_json,
                       coalesce(sd.metadata_json, '{}'::jsonb) as source_metadata_json
                from chunks c
                left join source_documents sd on sd.id = c.source_document_id
                where c.version_id = %s
                order by c.path asc, c.start_line asc, c.ordinal asc, c.id asc
                """,
                (version_id,),
            )
            rows = cursor.fetchall()
        output: list[dict[str, Any]] = []
        for row in rows:
            output.append(
                {
                    "id": row[0],
                    "source_document_id": row[1],
                    "path": row[2],
                    "start_line": row[3],
                    "end_line": row[4],
                    "source_url": row[5],
                    "ordinal": row[6],
                    "chunk_key": row[7],
                    "parent_chunk_key": row[8],
                    "chunk_sha": row[9],
                    "content_sha": row[10],
                    "heading_path": row[11] or [],
                    "symbols": row[12] or [],
                    "content_type": row[13],
                    "quality_score": row[14],
                    "token_count": row[15],
                    "source_anchor": row[16],
                    "content": row[17],
                    "dedupe_canonical": row[18],
                    "source_title": row[19],
                    "source_type": row[20],
                    "document_role": row[21],
                    "product": row[22],
                    "product_confidence": row[23],
                    "language": row[24],
                    "source_priority": row[25],
                    "metadata_json": merge_metadata(
                        {
                            **(row[26] if isinstance(row[26], dict) else {}),
                            "source_type": row[20],
                            "document_role": row[21],
                            "product": row[22],
                            "product_confidence": row[23],
                            "language": row[24],
                        },
                        row[27],
                    ),
                }
            )
        return output

    def resolve_chunk_sections(self, version_id: int, section_ids: dict[str, int]) -> None:
        for section_key, section_id in section_ids.items():
            if not section_key:
                continue
            self.execute(
                """
                update chunks
                   set source_section_id = %s
                 where version_id = %s
                   and metadata_json->>'source_section_key' = %s
                """,
                (section_id, version_id, section_key),
            )

    def replace_source_sections(self, version_id: int, sections: list[Any], source_ids: dict[str, int]) -> dict[str, int]:
        section_ids: dict[str, int] = {}
        for section in sections:
            section_key = str(field(section, "section_key") or "")
            if not section_key:
                continue
            metadata = field(section, "metadata_json", {}) if isinstance(field(section, "metadata_json", {}), dict) else {}
            section_id = self.scalar(
                """
                insert into source_sections(
                  version_id, source_document_id, section_key, path, source_url, source_anchor,
                  title, heading_path, document_role, content_type, product, product_confidence,
                  language, depth, start_line, end_line, content, content_sha,
                  has_code, has_endpoint_shape, has_signature_shape,
                  token_count, quality_score, metadata_json
                )
                values (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s::jsonb, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s,
                  %s, %s, %s::jsonb
                )
                on conflict (version_id, section_key) do update
                  set source_document_id = excluded.source_document_id,
                      path = excluded.path,
                      source_url = excluded.source_url,
                      source_anchor = excluded.source_anchor,
                      title = excluded.title,
                      heading_path = excluded.heading_path,
                      document_role = excluded.document_role,
                      content_type = excluded.content_type,
                      product = excluded.product,
                      product_confidence = excluded.product_confidence,
                      language = excluded.language,
                      depth = excluded.depth,
                      start_line = excluded.start_line,
                      end_line = excluded.end_line,
                      content = excluded.content,
                      content_sha = excluded.content_sha,
                      has_code = excluded.has_code,
                      has_endpoint_shape = excluded.has_endpoint_shape,
                      has_signature_shape = excluded.has_signature_shape,
                      token_count = excluded.token_count,
                      quality_score = excluded.quality_score,
                      metadata_json = excluded.metadata_json
                returning id
                """,
                (
                    version_id,
                    source_ids.get(source_document_key_from_surface(section)) or field(section, "source_document_id"),
                    section_key,
                    str(field(section, "path", "")),
                    nullable_string(field(section, "source_url")),
                    nullable_string(field(section, "source_anchor")),
                    str(field(section, "title", "")) or "Documentation section",
                    json.dumps(list_of_strings(field(section, "heading_path"))),
                    str(field(section, "document_role", metadata.get("document_role") or "unknown")),
                    str(field(section, "content_type", "prose")),
                    str(field(section, "product", metadata.get("product") or "")),
                    float(field(section, "product_confidence", metadata.get("product_confidence") or 0) or 0),
                    str(field(section, "language", metadata.get("language") or "")),
                    int(field(section, "depth", len(list_of_strings(field(section, "heading_path")))) or 0),
                    int(field(section, "start_line", 1) or 1),
                    optional_int(field(section, "end_line")),
                    str(field(section, "content", "")),
                    nullable_string(field(section, "content_sha", metadata.get("content_sha"))),
                    bool(field(section, "has_code", metadata.get("has_code") or False)),
                    bool(field(section, "has_endpoint_shape", metadata.get("has_endpoint_shape") or False)),
                    bool(field(section, "has_signature_shape", metadata.get("has_signature_shape") or False)),
                    int(field(section, "token_count", token_count(str(field(section, "content", "")))) or 0),
                    float(field(section, "quality_score", 1) or 1),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            section_ids[section_key] = section_id
        self.delete_stale_surface_rows("source_sections", "section_key", version_id, list(section_ids))
        return section_ids

    def replace_code_examples(
        self,
        version_id: int,
        examples: list[dict[str, Any]],
        source_ids: dict[str, int],
        section_ids: dict[str, int],
    ) -> dict[str, int]:
        example_ids: dict[str, int] = {}
        for example in examples:
            key = str(example.get("example_key") or "")
            if not key:
                continue
            metadata = example.get("metadata_json") if isinstance(example.get("metadata_json"), dict) else {}
            example_id = self.scalar(
                """
                insert into code_examples(
                  version_id, source_document_id, source_section_id, example_key, source_type,
                  document_role, product, product_confidence, language, title, description,
                  caption, code, imports_json, symbols_json, task_tags_json, required_env_json,
                  required_params_json, source_url, source_anchor, source_chunk_ids_json,
                  token_count, quality_score, confidence, metadata_json
                )
                values (
                  %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                  %s::jsonb, %s, %s, %s::jsonb,
                  %s, %s, %s, %s::jsonb
                )
                on conflict (version_id, example_key) do update
                  set source_document_id = excluded.source_document_id,
                      source_section_id = excluded.source_section_id,
                      source_type = excluded.source_type,
                      document_role = excluded.document_role,
                      product = excluded.product,
                      product_confidence = excluded.product_confidence,
                      language = excluded.language,
                      title = excluded.title,
                      description = excluded.description,
                      caption = excluded.caption,
                      code = excluded.code,
                      imports_json = excluded.imports_json,
                      symbols_json = excluded.symbols_json,
                      task_tags_json = excluded.task_tags_json,
                      required_env_json = excluded.required_env_json,
                      required_params_json = excluded.required_params_json,
                      source_url = excluded.source_url,
                      source_anchor = excluded.source_anchor,
                      source_chunk_ids_json = excluded.source_chunk_ids_json,
                      token_count = excluded.token_count,
                      quality_score = excluded.quality_score,
                      confidence = excluded.confidence,
                      metadata_json = excluded.metadata_json
                returning id
                """,
                (
                    version_id,
                    source_ids.get(source_document_key_from_surface(example)),
                    section_ids.get(str(example.get("source_section_key") or "")),
                    key,
                    str(example.get("source_type") or metadata.get("source_type") or "website_url"),
                    str(example.get("document_role") or metadata.get("document_role") or "unknown"),
                    str(example.get("product") or metadata.get("product") or ""),
                    float(example.get("product_confidence") or metadata.get("product_confidence") or 0),
                    str(example.get("language") or ""),
                    str(example.get("title") or "Code example"),
                    str(example.get("description") or ""),
                    str(example.get("caption") or ""),
                    str(example.get("code") or ""),
                    list_json(example.get("imports_json")),
                    list_json(example.get("symbols_json")),
                    list_json(example.get("task_tags_json")),
                    list_json(example.get("required_env_json")),
                    list_json(example.get("required_params_json")),
                    nullable_string(example.get("source_url")),
                    nullable_string(example.get("source_anchor")),
                    list_json(example.get("source_chunk_ids_json")),
                    int(example.get("token_count") or token_count(str(example.get("code") or ""))),
                    float(example.get("quality_score") or 1),
                    float(example.get("confidence") or 0),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            example_ids[key] = example_id
        self.delete_stale_surface_rows("code_examples", "example_key", version_id, list(example_ids))
        return example_ids

    def replace_api_operations(
        self,
        version_id: int,
        operations: list[dict[str, Any]],
        source_ids: dict[str, int],
        section_ids: dict[str, int],
    ) -> dict[str, int]:
        operation_ids: dict[str, int] = {}
        for operation in operations:
            key = str(operation.get("operation_key") or "")
            if not key:
                continue
            metadata = operation.get("metadata_json") if isinstance(operation.get("metadata_json"), dict) else {}
            operation_id = self.scalar(
                """
                insert into api_operations(
                  version_id, source_document_id, source_section_id, operation_key, product, product_confidence,
                  operation_id, operation_name, operation_kind, http_method, endpoint, route,
                  tags_json, summary, description, required_params_json, optional_params_json,
                  request_schema_json, response_schema_json, errors_json, auth_requirements_json,
                  source_url, source_anchor, source_chunk_ids_json,
                  token_count, quality_score, confidence, metadata_json
                )
                values (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s,
                  %s::jsonb, %s, %s, %s::jsonb, %s::jsonb,
                  %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                  %s, %s, %s::jsonb,
                  %s, %s, %s, %s::jsonb
                )
                on conflict (version_id, operation_key) do update
                  set source_document_id = excluded.source_document_id,
                      source_section_id = excluded.source_section_id,
                      product = excluded.product,
                      product_confidence = excluded.product_confidence,
                      operation_id = excluded.operation_id,
                      operation_name = excluded.operation_name,
                      operation_kind = excluded.operation_kind,
                      http_method = excluded.http_method,
                      endpoint = excluded.endpoint,
                      route = excluded.route,
                      tags_json = excluded.tags_json,
                      summary = excluded.summary,
                      description = excluded.description,
                      required_params_json = excluded.required_params_json,
                      optional_params_json = excluded.optional_params_json,
                      request_schema_json = excluded.request_schema_json,
                      response_schema_json = excluded.response_schema_json,
                      errors_json = excluded.errors_json,
                      auth_requirements_json = excluded.auth_requirements_json,
                      source_url = excluded.source_url,
                      source_anchor = excluded.source_anchor,
                      source_chunk_ids_json = excluded.source_chunk_ids_json,
                      token_count = excluded.token_count,
                      quality_score = excluded.quality_score,
                      confidence = excluded.confidence,
                      metadata_json = excluded.metadata_json
                returning id
                """,
                (
                    version_id,
                    source_ids.get(source_document_key_from_surface(operation)),
                    section_ids.get(str(operation.get("source_section_key") or metadata.get("source_section_key") or "")),
                    key,
                    str(operation.get("product") or metadata.get("product") or ""),
                    float(operation.get("product_confidence") or metadata.get("product_confidence") or 0),
                    str(operation.get("operation_id") or ""),
                    str(operation.get("operation_name") or operation.get("operation_id") or operation.get("endpoint") or "API operation"),
                    str(operation.get("operation_kind") or "operation"),
                    str(operation.get("http_method") or ""),
                    str(operation.get("endpoint") or ""),
                    str(operation.get("route") or operation.get("endpoint") or ""),
                    list_json(operation.get("tags_json")),
                    str(operation.get("summary") or ""),
                    str(operation.get("description") or ""),
                    list_json(operation.get("required_params_json")),
                    list_json(operation.get("optional_params_json")),
                    dict_json(operation.get("request_schema_json")),
                    dict_json(operation.get("response_schema_json")),
                    list_json(operation.get("errors_json")),
                    list_json(operation.get("auth_requirements_json")),
                    nullable_string(operation.get("source_url")),
                    nullable_string(operation.get("source_anchor")),
                    list_json(operation.get("source_chunk_ids_json")),
                    int(operation.get("token_count") or token_count(text_for_search(operation.get("summary"), operation.get("description")))),
                    float(operation.get("quality_score") or 1),
                    float(operation.get("confidence") or 0),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            operation_ids[key] = operation_id
        self.delete_stale_surface_rows("api_operations", "operation_key", version_id, list(operation_ids))
        return operation_ids

    def replace_sdk_methods(
        self,
        version_id: int,
        methods: list[dict[str, Any]],
        source_ids: dict[str, int],
        section_ids: dict[str, int],
    ) -> dict[str, int]:
        method_ids: dict[str, int] = {}
        for method in methods:
            key = str(method.get("method_key") or "")
            if not key:
                continue
            metadata = method.get("metadata_json") if isinstance(method.get("metadata_json"), dict) else {}
            method_id = self.scalar(
                """
                insert into sdk_methods(
                  version_id, source_document_id, source_section_id, method_key, product, product_confidence,
                  language, import_path, module_path, sdk_class, sdk_method, symbol_name,
                  signature, description, required_params_json, optional_params_json,
                  return_type, errors_json, source_url, source_anchor, source_chunk_ids_json,
                  public_api, generated, quality_score, confidence, metadata_json
                )
                values (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s::jsonb, %s::jsonb,
                  %s, %s::jsonb, %s, %s, %s::jsonb,
                  %s, %s, %s, %s, %s::jsonb
                )
                on conflict (version_id, method_key) do update
                  set source_document_id = excluded.source_document_id,
                      source_section_id = excluded.source_section_id,
                      product = excluded.product,
                      product_confidence = excluded.product_confidence,
                      language = excluded.language,
                      import_path = excluded.import_path,
                      module_path = excluded.module_path,
                      sdk_class = excluded.sdk_class,
                      sdk_method = excluded.sdk_method,
                      symbol_name = excluded.symbol_name,
                      signature = excluded.signature,
                      description = excluded.description,
                      required_params_json = excluded.required_params_json,
                      optional_params_json = excluded.optional_params_json,
                      return_type = excluded.return_type,
                      errors_json = excluded.errors_json,
                      source_url = excluded.source_url,
                      source_anchor = excluded.source_anchor,
                      source_chunk_ids_json = excluded.source_chunk_ids_json,
                      public_api = excluded.public_api,
                      generated = excluded.generated,
                      quality_score = excluded.quality_score,
                      confidence = excluded.confidence,
                      metadata_json = excluded.metadata_json
                returning id
                """,
                (
                    version_id,
                    source_ids.get(source_document_key_from_surface(method)),
                    section_ids.get(str(method.get("source_section_key") or metadata.get("source_section_key") or "")),
                    key,
                    str(method.get("product") or metadata.get("product") or ""),
                    float(method.get("product_confidence") or metadata.get("product_confidence") or 0),
                    str(method.get("language") or ""),
                    str(method.get("import_path") or ""),
                    str(method.get("module_path") or ""),
                    str(method.get("sdk_class") or ""),
                    str(method.get("sdk_method") or ""),
                    str(method.get("symbol_name") or method.get("sdk_method") or method.get("sdk_class") or "SDK method"),
                    str(method.get("signature") or ""),
                    str(method.get("description") or ""),
                    list_json(method.get("required_params_json")),
                    list_json(method.get("optional_params_json")),
                    str(method.get("return_type") or ""),
                    list_json(method.get("errors_json")),
                    nullable_string(method.get("source_url")),
                    nullable_string(method.get("source_anchor")),
                    list_json(method.get("source_chunk_ids_json")),
                    bool(method.get("public_api", True)),
                    bool(method.get("generated", False)),
                    float(method.get("quality_score") or 1),
                    float(method.get("confidence") or 0),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            method_ids[key] = method_id
        self.delete_stale_surface_rows("sdk_methods", "method_key", version_id, list(method_ids))
        return method_ids

    def replace_agent_recipes(self, version_id: int, recipes: list[dict[str, Any]]) -> None:
        recipe_keys: list[str] = []
        for recipe in recipes:
            key = str(recipe.get("recipe_key") or "")
            if not key:
                continue
            recipe_keys.append(key)
            metadata = recipe.get("metadata_json") if isinstance(recipe.get("metadata_json"), dict) else {}
            self.execute(
                """
                insert into agent_recipes(
                  version_id, recipe_key, product, product_confidence, title, task_kind,
                  language, summary, code, info, required_env_json, required_params_json,
                  source_api_operation_ids_json, source_sdk_method_ids_json,
                  source_code_example_ids_json, source_section_ids_json, source_chunk_ids_json,
                  source_urls_json, evidence_hash, llm_model, llm_enriched,
                  confidence, quality_score, token_count, metadata_json
                )
                values (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s::jsonb, %s::jsonb,
                  %s::jsonb, %s::jsonb,
                  %s::jsonb, %s::jsonb, %s::jsonb,
                  %s::jsonb, %s, %s, %s,
                  %s, %s, %s, %s::jsonb
                )
                on conflict (version_id, recipe_key) do update
                  set product = excluded.product,
                      product_confidence = excluded.product_confidence,
                      title = excluded.title,
                      task_kind = excluded.task_kind,
                      language = excluded.language,
                      summary = excluded.summary,
                      code = excluded.code,
                      info = excluded.info,
                      required_env_json = excluded.required_env_json,
                      required_params_json = excluded.required_params_json,
                      source_api_operation_ids_json = excluded.source_api_operation_ids_json,
                      source_sdk_method_ids_json = excluded.source_sdk_method_ids_json,
                      source_code_example_ids_json = excluded.source_code_example_ids_json,
                      source_section_ids_json = excluded.source_section_ids_json,
                      source_chunk_ids_json = excluded.source_chunk_ids_json,
                      source_urls_json = excluded.source_urls_json,
                      evidence_hash = excluded.evidence_hash,
                      llm_model = excluded.llm_model,
                      llm_enriched = excluded.llm_enriched,
                      confidence = excluded.confidence,
                      quality_score = excluded.quality_score,
                      token_count = excluded.token_count,
                      metadata_json = excluded.metadata_json
                """,
                (
                    version_id,
                    key,
                    str(recipe.get("product") or ""),
                    float(recipe.get("product_confidence") or 0),
                    str(recipe.get("title") or "Recipe"),
                    str(recipe.get("task_kind") or "operation"),
                    str(recipe.get("language") or ""),
                    str(recipe.get("summary") or ""),
                    nullable_string(recipe.get("code")),
                    str(recipe.get("info") or ""),
                    list_json(recipe.get("required_env_json")),
                    list_json(recipe.get("required_params_json")),
                    list_json(recipe.get("source_api_operation_ids_json")),
                    list_json(recipe.get("source_sdk_method_ids_json")),
                    list_json(recipe.get("source_code_example_ids_json")),
                    list_json(recipe.get("source_section_ids_json")),
                    list_json(recipe.get("source_chunk_ids_json")),
                    list_json(recipe.get("source_urls_json")),
                    str(recipe.get("evidence_hash") or ""),
                    str(recipe.get("llm_model") or ""),
                    bool(recipe.get("llm_enriched", False)),
                    float(recipe.get("confidence") or 0),
                    float(recipe.get("quality_score") or 1),
                    int(recipe.get("token_count") or token_count(text_for_search(recipe.get("summary"), recipe.get("code"), recipe.get("info")))),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
        self.delete_stale_surface_rows("agent_recipes", "recipe_key", version_id, recipe_keys)

    def delete_stale_surface_rows(self, table_name: str, key_column: str, version_id: int, current_keys: list[str]) -> None:
        self.delete_stale_rows(table_name, key_column, version_id, current_keys)
