"""
Reasoning Store - SQLite persistence of LLM rationales keyed by keccak256 hash.

Every trade executed through the vault commits only the hash on-chain; the full
reasoning text lives here so any caller can verify the hash locally.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from web3 import Web3

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "reasoning.db"


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reasoning (
                hash TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                token_in TEXT,
                token_out TEXT,
                tx_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


_init_db()


@contextmanager
def _conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def compute_hash(text: str) -> str:
    """keccak256 of UTF-8 text, matching Solidity `keccak256(bytes(text))`.
    Always returns a 0x-prefixed lowercase hex string."""
    h = Web3.keccak(text=text).hex()
    return h if h.startswith("0x") else "0x" + h


def store(
    text: str,
    confidence: int,
    token_in: Optional[str] = None,
    token_out: Optional[str] = None,
    tx_hash: Optional[str] = None,
) -> str:
    """Save reasoning and return its hex hash (0x-prefixed)."""
    h = compute_hash(text)
    with _conn() as c:
        c.execute(
            """
            INSERT OR REPLACE INTO reasoning
                (hash, text, confidence, token_in, token_out, tx_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (h, text, confidence, token_in, token_out, tx_hash),
        )
    return h


def update_tx_hash(reasoning_hash: str, tx_hash: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE reasoning SET tx_hash = ? WHERE hash = ?",
            (tx_hash, reasoning_hash),
        )


def get(reasoning_hash: str) -> Optional[dict]:
    """Fetch reasoning row by hash, or None if missing. Hash may be with/without 0x."""
    h = reasoning_hash.lower()
    if not h.startswith("0x"):
        h = "0x" + h
    with _conn() as c:
        row = c.execute("SELECT * FROM reasoning WHERE hash = ?", (h,)).fetchone()
        return dict(row) if row else None


def list_recent(limit: int = 20) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM reasoning ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
