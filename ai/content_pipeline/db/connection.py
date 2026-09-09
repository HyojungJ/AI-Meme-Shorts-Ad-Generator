import os
import threading
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv

load_dotenv()

_pool: ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    database=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                )
    return _pool


class _PooledConnection:
    """conn.close() 호출 시 풀에 반환하는 래퍼."""

    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool
        self._returned = False

    def close(self):
        if not self._returned:
            self._returned = True
            self._pool.putconn(self._conn)

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_db_connection():
    """커넥션 풀에서 연결을 가져옴. close() 시 풀에 반환."""
    pool = _get_pool()
    conn = pool.getconn()
    return _PooledConnection(conn, pool)


@contextmanager
def db_cursor():
    """try-finally-close 패턴을 대체하는 컨텍스트 매니저."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_db_connection() -> tuple[str, str, str]:
    with db_cursor() as cur:
        cur.execute("SELECT current_database(), current_user, now()")
        db_name, db_user, now = cur.fetchone()
        return str(db_name), str(db_user), str(now)
