from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from oz_api.db import postgres_connection


@dataclass(frozen=True)
class AuthStore:
    database: str = "oz"
    database_url: str | None = None

    @classmethod
    def from_env(cls) -> "AuthStore | None":
        database_url = os.environ.get("OZ_DATABASE_URL") or os.environ.get("DATABASE_URL")
        if not database_url:
            return None
        return cls(database_url=database_url, database=os.environ.get("OZ_DB_NAME", "oz"))

    def execute(self, sql: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.execute_postgres(sql, parameters or {})

    def one(self, sql: str, parameters: dict[str, Any] | None = None) -> dict[str, Any] | None:
        rows = self.execute(sql, parameters)
        return rows[0] if rows else None

    def execute_postgres(self, sql: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        connection = postgres_connection(self.database_url)
        if connection is None:
            raise RuntimeError("Postgres client is unavailable")
        query = named_to_pyformat(sql)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query, parameters)
                if cursor.description is None:
                    return []
                columns = [getattr(column, "name", column[0]) for column in cursor.description]
                return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

def named_to_pyformat(sql: str) -> str:
    return re.sub(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", sql)
