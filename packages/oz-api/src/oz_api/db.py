from __future__ import annotations

import logging
import os
from threading import Lock
from typing import Any

LOGGER = logging.getLogger(__name__)

_POOLS: dict[str, Any] = {}
_POOLS_LOCK = Lock()


class PooledConnection:
    def __init__(self, pool: Any, connection: Any) -> None:
        self._pool = pool
        self._connection = connection
        self._returned = False

    def __enter__(self) -> "PooledConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self.close()
        return False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        return self._connection.cursor(*args, **kwargs)

    def close(self) -> None:
        if self._returned:
            return
        self._returned = True
        self._pool.putconn(self._connection)

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


def postgres_connection(database_url: str | None) -> PooledConnection | None:
    if not database_url:
        return None
    try:
        pool = postgres_pool(database_url)
        return PooledConnection(pool, pool.getconn())
    except Exception as exc:
        LOGGER.warning("postgres connection failed: %s", exc)
        return None


def postgres_pool(database_url: str) -> Any:
    with _POOLS_LOCK:
        pool = _POOLS.get(database_url)
        if pool is not None:
            return pool
        try:
            from psycopg_pool import ConnectionPool  # type: ignore
        except ImportError as exc:
            raise RuntimeError("psycopg_pool package is unavailable") from exc
        pool = ConnectionPool(
            conninfo=database_url,
            min_size=int_env("OZ_DB_POOL_MIN_SIZE", 1),
            max_size=int_env("OZ_DB_POOL_MAX_SIZE", 20),
            timeout=float_env("OZ_DB_POOL_TIMEOUT_SECONDS", 10.0),
            open=True,
        )
        _POOLS[database_url] = pool
        return pool


def close_postgres_pools() -> None:
    with _POOLS_LOCK:
        pools = list(_POOLS.values())
        _POOLS.clear()
    for pool in pools:
        try:
            pool.close()
        except Exception as exc:
            LOGGER.warning("failed to close postgres pool: %s", exc)


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
