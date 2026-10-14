"""Natural-language, read-only interface for the competitive game database."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = APP_DIR / "Competitive_Game_Schema.sql"
SEED_PATH = APP_DIR / "setupData.sql"
DEFAULT_DB_PATH = APP_DIR / "competitive_game.sqlite3"
LOG_DIR = APP_DIR / "responses"
DEFAULT_MODEL = "gpt-4o-mini"
MAX_RESULT_ROWS = 100
QUERY_TIMEOUT_SECONDS = 2.0

SAMPLE_QUESTIONS = (
    "Which player has the most total kills?",
    "Which teams are in the ongoing game, and what colors are they?",
    "How many goals and zones has each team captured?",
    "Which players have more assists than deaths?",
    "Where are the active objectives in the ongoing game?",
    "Which team members are captains?",
)


class QueryRejected(ValueError):
    """Raised when model-generated SQL is not a single read-only query."""


def initialize_database(db_path: Path = DEFAULT_DB_PATH, *, reset: bool = False) -> None:
    """Create and seed the SQLite database if it does not exist."""
    db_path = db_path.resolve()
    if reset and db_path.exists():
        db_path.unlink()
    if db_path.exists():
        return

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    seed_data = SEED_PATH.read_text(encoding="utf-8")
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)
        connection.executescript(seed_data)
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Seed data has foreign-key violations: {violations}")
        connection.commit()
    except Exception:
        connection.close()
        db_path.unlink(missing_ok=True)
        raise
    finally:
        if db_path.exists():
            connection.close()


def normalize_sql(sql: str) -> str:
    """Validate the shape of a model-produced SQLite SELECT statement."""
    query = sql.strip()
    fenced = re.fullmatch(r"```(?:sql|sqlite)?\s*(.*?)\s*```", query, re.DOTALL | re.IGNORECASE)
    if fenced:
        query = fenced.group(1).strip()

    query = query.rstrip(";").strip()
    if not query:
        raise QueryRejected("The model returned an empty query.")
    if ";" in query:
        raise QueryRejected("Only one SQL statement is allowed.")
    if not re.match(r"^(SELECT|WITH)\b", query, re.IGNORECASE):
        raise QueryRejected("Only SELECT statements and read-only CTEs are allowed.")
    if re.search(r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM)\b", query, re.IGNORECASE):
        raise QueryRejected("The query contains a prohibited SQL operation.")
    return query


def run_read_only_query(
    sql: str,
    db_path: Path = DEFAULT_DB_PATH,
    *,
    max_rows: int = MAX_RESULT_ROWS,
) -> tuple[list[str], list[list[Any]], bool]:
    """Execute one query through an OS-level read-only SQLite connection."""
    query = normalize_sql(sql)
    database_uri = f"{db_path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    started = time.monotonic()

    def stop_long_query() -> int:
        return int(time.monotonic() - started > QUERY_TIMEOUT_SECONDS)

    try:
        connection.execute("PRAGMA query_only = ON")
        connection.set_progress_handler(stop_long_query, 1_000)
        cursor = connection.execute(query)
        columns = [description[0] for description in cursor.description or ()]
        rows = cursor.fetchmany(max_rows + 1)
        truncated = len(rows) > max_rows
        return columns, [list(row) for row in rows[:max_rows]], truncated
    finally:
        connection.close()


def create_openai_client() -> Any:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. In PowerShell, run: "
            '$env:OPENAI_API_KEY="your-key"'
        )
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The OpenAI package is not installed. Run: py -m pip install -r requirements.txt"
        ) from exc
    return OpenAI()


def generate_sql(client: Any, question: str, schema: str, model: str) -> str:
    response = client.responses.create(
        model=model,
        instructions=(
            "Translate the employee's question into exactly one read-only SQLite query. "
            "Use only the supplied schema. Never modify the database. Prefer descriptive "
            "columns, joining identifiers to names or usernames when that makes the result "
            "easier to understand. Return SQL without Markdown."
        ),
        input=f"DATABASE SCHEMA:\n{schema}\n\nEMPLOYEE QUESTION:\n{question}",
        text={
            "format": {
                "type": "json_schema",
                "name": "database_query",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "One read-only SQLite SELECT statement.",
                        }
                    },
                    "required": ["sql"],
                    "additionalProperties": False,
                },
            }
        },
    )
    try:
        return normalize_sql(json.loads(response.output_text)["sql"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError("The model did not return the expected structured SQL output.") from exc


def generate_friendly_answer(
    client: Any,
    question: str,
    sql: str,
    columns: list[str],
    rows: list[list[Any]],
    truncated: bool,
    model: str,
) -> str:
    result = {
        "columns": columns,
        "rows": rows,
        "truncated_after_rows": MAX_RESULT_ROWS if truncated else None,
    }
    response = client.responses.create(
        model=model,
        instructions=(
            "Answer the employee's original question using only the supplied SQL result. "
            "Be concise, mention relevant names rather than unexplained IDs, and say when "
            "no rows matched. Do not invent facts or suggest another query."
        ),
        input=(
            f"ORIGINAL QUESTION:\n{question}\n\nSQL USED:\n{sql}\n\n"
            f"SQL RESULT:\n{json.dumps(result, ensure_ascii=False)}"
        ),
    )
    return response.output_text.strip()


def write_log(record: dict[str, Any]) -> Path:
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = LOG_DIR / f"response_{timestamp}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def answer_question(client: Any, question: str, model: str, db_path: Path) -> dict[str, Any]:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    record: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "question": question,
    }
    try:
        sql = generate_sql(client, question, schema, model)
        columns, rows, truncated = run_read_only_query(sql, db_path)
        answer = generate_friendly_answer(
            client, question, sql, columns, rows, truncated, model
        )
        record.update(
            sql=sql,
            columns=columns,
            rows=rows,
            truncated=truncated,
            answer=answer,
            error=None,
        )
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    record["log_path"] = str(write_log(record))
    return record


def print_result(record: dict[str, Any]) -> None:
    if record.get("error"):
        print(f"Error: {record['error']}")
    else:
        print(f"\nSQL:\n{record['sql']}")
        print(f"\nAnswer:\n{record['answer']}")
    print(f"\nLog: {record['log_path']}")


def interactive_loop(client: Any, model: str, db_path: Path) -> None:
    print("Competitive Game Database Assistant")
    print("Ask a question, type 'examples' for ideas, or type 'quit' to exit.")
    while True:
        try:
            question = input("\nQuestion> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if question.lower() in {"quit", "exit"}:
            print("Goodbye.")
            return
        if question.lower() == "examples":
            print("\n".join(f"- {item}" for item in SAMPLE_QUESTIONS))
            continue
        if not question:
            continue
        print_result(answer_question(client, question, model, db_path))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask natural-language questions about the competitive game database."
    )
    parser.add_argument("--question", help="Ask one question and exit.")
    parser.add_argument(
        "--demo", action="store_true", help="Run the six documented sample questions."
    )
    parser.add_argument(
        "--init-only", action="store_true", help="Initialize the database without using AI."
    )
    parser.add_argument(
        "--reset-db", action="store_true", help="Recreate the generated SQLite database."
    )
    parser.add_argument(
        "--database", type=Path, default=DEFAULT_DB_PATH, help="SQLite database path."
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="OpenAI model (or set OPENAI_MODEL).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        initialize_database(args.database, reset=args.reset_db)
        if args.init_only:
            print(f"Database ready: {args.database.resolve()}")
            return 0
        client = create_openai_client()
        if args.demo:
            for question in SAMPLE_QUESTIONS:
                print(f"\n{'=' * 72}\nQuestion: {question}")
                print_result(answer_question(client, question, args.model, args.database))
        elif args.question:
            print_result(answer_question(client, args.question, args.model, args.database))
        else:
            interactive_loop(client, args.model, args.database)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
