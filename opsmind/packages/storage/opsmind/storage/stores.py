from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime

import psycopg
import redis

from opsmind.contracts.v1.models import ConversationState, Message, ToolResult


class ConversationStateStore(ABC):
    @abstractmethod
    def get(self, conversation_id: str) -> ConversationState | None: ...

    @abstractmethod
    def create(self, initial_state: ConversationState) -> ConversationState: ...

    @abstractmethod
    def save(self, state: ConversationState) -> None: ...


class TranscriptStore(ABC):
    @abstractmethod
    def append_message(self, conversation_id: str, message: Message) -> None: ...

    @abstractmethod
    def list_messages(self, conversation_id: str, limit: int, offset: int) -> list[Message]: ...


class ToolResultStore(ABC):
    @abstractmethod
    def store_tool_result(self, conversation_id: str, tool_result: ToolResult) -> str: ...

    @abstractmethod
    def get_tool_result(self, ref: str) -> ToolResult | None: ...


class InMemoryStore(ConversationStateStore, TranscriptStore, ToolResultStore):
    def __init__(self) -> None:
        self.states: dict[str, ConversationState] = {}
        self.transcripts: dict[str, list[Message]] = {}
        self.tool_results: dict[str, ToolResult] = {}

    def get(self, conversation_id: str) -> ConversationState | None:
        return self.states.get(conversation_id)

    def create(self, initial_state: ConversationState) -> ConversationState:
        self.states[initial_state.conversation_id] = initial_state
        self.transcripts[initial_state.conversation_id] = []
        return initial_state

    def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.utcnow()
        self.states[state.conversation_id] = state

    def append_message(self, conversation_id: str, message: Message) -> None:
        self.transcripts.setdefault(conversation_id, []).append(message)

    def list_messages(self, conversation_id: str, limit: int, offset: int) -> list[Message]:
        return self.transcripts.get(conversation_id, [])[offset : offset + limit]

    def store_tool_result(self, conversation_id: str, tool_result: ToolResult) -> str:
        ref = f"{conversation_id}:{tool_result.tool_call_id}"
        self.tool_results[ref] = tool_result
        return ref

    def get_tool_result(self, ref: str) -> ToolResult | None:
        return self.tool_results.get(ref)


class RedisPostgresStore(ConversationStateStore, TranscriptStore, ToolResultStore):
    def __init__(self, redis_url: str, postgres_dsn: str) -> None:
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.pg_dsn = postgres_dsn
        self._init_tables()

    def _init_tables(self) -> None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transcripts (
                      id SERIAL PRIMARY KEY,
                      conversation_id TEXT NOT NULL,
                      message_json JSONB NOT NULL,
                      created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS tool_results (
                      ref TEXT PRIMARY KEY,
                      conversation_id TEXT NOT NULL,
                      result_json JSONB NOT NULL,
                      created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
            conn.commit()

    def get(self, conversation_id: str) -> ConversationState | None:
        raw = self.redis.get(f"state:{conversation_id}")
        if not raw:
            return None
        return ConversationState.model_validate_json(raw)

    def create(self, initial_state: ConversationState) -> ConversationState:
        self.save(initial_state)
        return initial_state

    def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.utcnow()
        self.redis.set(f"state:{state.conversation_id}", state.model_dump_json())

    def append_message(self, conversation_id: str, message: Message) -> None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO transcripts (conversation_id, message_json) VALUES (%s, %s)",
                    (conversation_id, json.dumps(message.model_dump(mode='json'))),
                )
            conn.commit()

    def list_messages(self, conversation_id: str, limit: int, offset: int) -> list[Message]:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT message_json FROM transcripts WHERE conversation_id=%s ORDER BY id LIMIT %s OFFSET %s",
                    (conversation_id, limit, offset),
                )
                rows = cur.fetchall()
        return [Message.model_validate(r[0]) for r in rows]

    def store_tool_result(self, conversation_id: str, tool_result: ToolResult) -> str:
        ref = f"{conversation_id}:{tool_result.tool_call_id}"
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tool_results (ref, conversation_id, result_json) VALUES (%s, %s, %s) ON CONFLICT (ref) DO UPDATE SET result_json=EXCLUDED.result_json",
                    (ref, conversation_id, json.dumps(tool_result.model_dump(mode='json'))),
                )
            conn.commit()
        return ref

    def get_tool_result(self, ref: str) -> ToolResult | None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT result_json FROM tool_results WHERE ref=%s", (ref,))
                row = cur.fetchone()
        if not row:
            return None
        return ToolResult.model_validate(row[0])


class PostgresStore(ConversationStateStore, TranscriptStore, ToolResultStore):
    """Postgres-only store: stores conversation state, transcripts and tool results in Postgres.

    This is used when Redis is not available and the user provides only a DATABASE_URL.
    """
    def __init__(self, postgres_dsn: str) -> None:
        self.pg_dsn = postgres_dsn
        self._init_tables()

    def _init_tables(self) -> None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS states (
                      conversation_id TEXT PRIMARY KEY,
                      state_json JSONB NOT NULL,
                      updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS transcripts (
                      id SERIAL PRIMARY KEY,
                      conversation_id TEXT NOT NULL,
                      message_json JSONB NOT NULL,
                      created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    CREATE TABLE IF NOT EXISTS tool_results (
                      ref TEXT PRIMARY KEY,
                      conversation_id TEXT NOT NULL,
                      result_json JSONB NOT NULL,
                      created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
            conn.commit()

    def get(self, conversation_id: str) -> ConversationState | None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT state_json FROM states WHERE conversation_id=%s", (conversation_id,))
                row = cur.fetchone()
        if not row:
            return None
        return ConversationState.model_validate(row[0])

    def create(self, initial_state: ConversationState) -> ConversationState:
        self.save(initial_state)
        return initial_state

    def save(self, state: ConversationState) -> None:
        state.updated_at = datetime.utcnow()
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO states (conversation_id, state_json, updated_at) VALUES (%s, %s, %s)"
                    " ON CONFLICT (conversation_id) DO UPDATE SET state_json=EXCLUDED.state_json, updated_at=EXCLUDED.updated_at",
                    (state.conversation_id, json.dumps(state.model_dump(mode="json")), state.updated_at),
                )
            conn.commit()

    def append_message(self, conversation_id: str, message: Message) -> None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO transcripts (conversation_id, message_json) VALUES (%s, %s)",
                    (conversation_id, json.dumps(message.model_dump(mode="json"))),
                )
            conn.commit()

    def list_messages(self, conversation_id: str, limit: int, offset: int) -> list[Message]:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT message_json FROM transcripts WHERE conversation_id=%s ORDER BY id LIMIT %s OFFSET %s",
                    (conversation_id, limit, offset),
                )
                rows = cur.fetchall()
        return [Message.model_validate(r[0]) for r in rows]

    def store_tool_result(self, conversation_id: str, tool_result: ToolResult) -> str:
        ref = f"{conversation_id}:{tool_result.tool_call_id}"
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tool_results (ref, conversation_id, result_json) VALUES (%s, %s, %s) ON CONFLICT (ref) DO UPDATE SET result_json=EXCLUDED.result_json",
                    (ref, conversation_id, json.dumps(tool_result.model_dump(mode="json"))),
                )
            conn.commit()
        return ref

    def get_tool_result(self, ref: str) -> ToolResult | None:
        with psycopg.connect(self.pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT result_json FROM tool_results WHERE ref=%s", (ref,))
                row = cur.fetchone()
        if not row:
            return None
        return ToolResult.model_validate(row[0])
