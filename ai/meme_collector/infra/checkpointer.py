import logging

from langgraph.checkpoint.memory import MemorySaver

from common.config import config

log = logging.getLogger(__name__)


def get_checkpointer(use_postgres=False):
    if not use_postgres:
        return MemorySaver()

    try:
        from langgraph.checkpoint.postgres import PostgresSaver

        conn_str = f"postgresql://{config.db.user}:{config.db.password}@{config.db.host}:{config.db.port}/{config.db.name}"
        checkpointer = PostgresSaver.from_conn_string(conn_str)
        checkpointer.setup()
        return checkpointer
    except Exception as e:
        log.warning(f"PostgreSQL checkpointer failed, using memory: {e}")
        return MemorySaver()
