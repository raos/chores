from __future__ import annotations

from db.connection import get_connection


def upsert_instances(rows: list[dict]) -> None:
    if not rows:
        return
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO chore_instances (chore_id, scheduled_date) VALUES (:chore_id, :scheduled_date)",
            rows,
        )


def get_instances_for_date(scheduled_date: str, child_id: int | None = None) -> list:
    with get_connection() as conn:
        if child_id is not None:
            return conn.execute(
                """
                SELECT ci.*, c.title, c.description, c.allowance_type,
                       c.fixed_amount, c.chore_weight, c.screen_time_hours,
                       c.assigned_to, ch.name AS child_name
                FROM chore_instances ci
                JOIN chores c ON ci.chore_id = c.id
                LEFT JOIN children ch ON c.assigned_to = ch.id
                WHERE ci.scheduled_date = ? AND c.assigned_to = ? AND c.is_active = 1
                ORDER BY c.title
                """,
                (scheduled_date, child_id),
            ).fetchall()
        return conn.execute(
            """
            SELECT ci.*, c.title, c.description, c.allowance_type,
                   c.fixed_amount, c.chore_weight, c.screen_time_hours,
                   c.assigned_to, ch.name AS child_name
            FROM chore_instances ci
            JOIN chores c ON ci.chore_id = c.id
            LEFT JOIN children ch ON c.assigned_to = ch.id
            WHERE ci.scheduled_date = ? AND c.is_active = 1
            ORDER BY c.title
            """,
            (scheduled_date,),
        ).fetchall()


def get_instances_for_week(week_start: str, week_end: str, child_id: int | None = None) -> list:
    with get_connection() as conn:
        if child_id is not None:
            return conn.execute(
                """
                SELECT ci.*, c.title, c.description, c.allowance_type,
                       c.fixed_amount, c.chore_weight, c.screen_time_hours,
                       c.assigned_to, ch.name AS child_name
                FROM chore_instances ci
                JOIN chores c ON ci.chore_id = c.id
                LEFT JOIN children ch ON c.assigned_to = ch.id
                WHERE ci.scheduled_date BETWEEN ? AND ?
                  AND c.assigned_to = ? AND c.is_active = 1
                ORDER BY ci.scheduled_date, c.title
                """,
                (week_start, week_end, child_id),
            ).fetchall()
        return conn.execute(
            """
            SELECT ci.*, c.title, c.description, c.allowance_type,
                   c.fixed_amount, c.chore_weight, c.screen_time_hours,
                   c.assigned_to, ch.name AS child_name
            FROM chore_instances ci
            JOIN chores c ON ci.chore_id = c.id
            LEFT JOIN children ch ON c.assigned_to = ch.id
            WHERE ci.scheduled_date BETWEEN ? AND ? AND c.is_active = 1
            ORDER BY ci.scheduled_date, c.title
            """,
            (week_start, week_end),
        ).fetchall()


def get_pending_approvals() -> list:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ci.*, c.title, c.description, c.allowance_type,
                   c.fixed_amount, c.chore_weight, c.screen_time_hours,
                   c.assigned_to, ch.name AS child_name
            FROM chore_instances ci
            JOIN chores c ON ci.chore_id = c.id
            LEFT JOIN children ch ON c.assigned_to = ch.id
            WHERE ci.status = 'completed_pending_approval' AND c.is_active = 1
            ORDER BY ci.scheduled_date DESC, ch.name, c.title
            """
        ).fetchall()


def transition_to_pending_approval(instance_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE chore_instances
            SET status = 'completed_pending_approval', completed_at = datetime('now')
            WHERE id = ? AND status = 'pending'
            """,
            (instance_id,),
        )
        return cur.rowcount == 1


def transition_to_approved(instance_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE chore_instances
            SET status = 'approved', approved_at = datetime('now')
            WHERE id = ? AND status IN ('pending', 'completed_pending_approval')
            """,
            (instance_id,),
        )
        return cur.rowcount == 1


def reset_to_pending(instance_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE chore_instances
            SET status = 'pending', completed_at = NULL, approved_at = NULL
            WHERE id = ? AND status = 'completed_pending_approval'
            """,
            (instance_id,),
        )
        return cur.rowcount == 1


def sweep_missed_chores(before_date: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE chore_instances
            SET status = 'missed'
            WHERE scheduled_date < ? AND status IN ('pending', 'completed_pending_approval')
            """,
            (before_date,),
        )
        return cur.rowcount


def get_instance(instance_id: int):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ci.*, c.title, c.description, c.allowance_type,
                   c.fixed_amount, c.chore_weight, c.screen_time_hours,
                   c.assigned_to, ch.name AS child_name,
                   ch.weekly_allowance_budget
            FROM chore_instances ci
            JOIN chores c ON ci.chore_id = c.id
            LEFT JOIN children ch ON c.assigned_to = ch.id
            WHERE ci.id = ?
            """,
            (instance_id,),
        ).fetchone()


def get_approved_weighted_instances_for_week(child_id: int, week_start: str, week_end: str) -> list:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ci.*, c.chore_weight, c.title
            FROM chore_instances ci
            JOIN chores c ON ci.chore_id = c.id
            WHERE ci.status = 'approved'
              AND c.assigned_to = ?
              AND c.allowance_type IN ('weighted', 'both')
              AND ci.scheduled_date BETWEEN ? AND ?
            """,
            (child_id, week_start, week_end),
        ).fetchall()
