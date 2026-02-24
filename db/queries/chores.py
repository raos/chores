from __future__ import annotations

from db.connection import get_connection


def list_chores(child_id: int | None = None, active_only: bool = True) -> list:
    with get_connection() as conn:
        conditions = []
        params = []
        if active_only:
            conditions.append("c.is_active = 1")
        if child_id is not None:
            conditions.append("c.assigned_to = ?")
            params.append(child_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return conn.execute(
            f"""
            SELECT c.*, ch.name AS child_name
            FROM chores c
            LEFT JOIN children ch ON c.assigned_to = ch.id
            {where}
            ORDER BY c.title
            """,
            params,
        ).fetchall()


def get_chore(chore_id: int):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT c.*, ch.name AS child_name
            FROM chores c
            LEFT JOIN children ch ON c.assigned_to = ch.id
            WHERE c.id = ?
            """,
            (chore_id,),
        ).fetchone()


def create_chore(
    title: str,
    description: str | None,
    assigned_to: int | None,
    created_by_role: str,
    recurrence_type: str,
    recurrence_days: str | None,
    start_date: str,
    end_date: str | None,
    allowance_type: str | None,
    fixed_amount: float | None,
    chore_weight: float | None,
    screen_time_hours: float,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO chores (
                title, description, assigned_to, created_by_role,
                recurrence_type, recurrence_days, start_date, end_date,
                allowance_type, fixed_amount, chore_weight, screen_time_hours
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title, description, assigned_to, created_by_role,
                recurrence_type, recurrence_days, start_date, end_date,
                allowance_type, fixed_amount, chore_weight, screen_time_hours,
            ),
        )
        return cur.lastrowid


def update_chore(
    chore_id: int,
    title: str,
    description: str | None,
    assigned_to: int | None,
    recurrence_type: str,
    recurrence_days: str | None,
    start_date: str,
    end_date: str | None,
    allowance_type: str | None,
    fixed_amount: float | None,
    chore_weight: float | None,
    screen_time_hours: float,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE chores SET
                title = ?, description = ?, assigned_to = ?,
                recurrence_type = ?, recurrence_days = ?,
                start_date = ?, end_date = ?,
                allowance_type = ?, fixed_amount = ?,
                chore_weight = ?, screen_time_hours = ?
            WHERE id = ?
            """,
            (
                title, description, assigned_to,
                recurrence_type, recurrence_days,
                start_date, end_date,
                allowance_type, fixed_amount,
                chore_weight, screen_time_hours,
                chore_id,
            ),
        )


def deactivate_chore(chore_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE chores SET is_active = 0 WHERE id = ?", (chore_id,)
        )


def prune_future_instances(chore_id: int, after_date: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM chore_instances
            WHERE chore_id = ? AND scheduled_date > ? AND status = 'pending'
            """,
            (chore_id, after_date),
        )
