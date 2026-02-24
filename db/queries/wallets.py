from __future__ import annotations

from db.connection import get_connection


def get_balance(child_id: int, transaction_type: str) -> float:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0.0) AS total
            FROM wallet_transactions
            WHERE child_id = ? AND transaction_type = ?
            """,
            (child_id, transaction_type),
        ).fetchone()
        return row["total"] if row else 0.0


def credit_wallet(
    child_id: int,
    chore_instance_id: int | None,
    transaction_type: str,
    amount: float,
    note: str | None = None,
) -> bool:
    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO wallet_transactions
                    (child_id, chore_instance_id, transaction_type, amount, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (child_id, chore_instance_id, transaction_type, amount, note),
            )
            return True
        except Exception:
            return False


def get_transactions(child_id: int, limit: int = 50) -> list:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT wt.*, ci.scheduled_date, c.title AS chore_title
            FROM wallet_transactions wt
            LEFT JOIN chore_instances ci ON wt.chore_instance_id = ci.id
            LEFT JOIN chores c ON ci.chore_id = c.id
            WHERE wt.child_id = ?
            ORDER BY wt.created_at DESC
            LIMIT ?
            """,
            (child_id, limit),
        ).fetchall()


def is_week_finalized(child_id: int, week_start: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM weekly_allowance_snapshots WHERE child_id = ? AND week_start_date = ?",
            (child_id, week_start),
        ).fetchone()
        return row is not None


def save_week_snapshot(
    child_id: int, week_start: str, total_payout: float, calculation_json: str
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO weekly_allowance_snapshots
                (child_id, week_start_date, total_payout, calculation_json)
            VALUES (?, ?, ?, ?)
            """,
            (child_id, week_start, total_payout, calculation_json),
        )
