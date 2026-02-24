from db.connection import get_connection


def list_children() -> list:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM children ORDER BY name"
        ).fetchall()


def get_child(child_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM children WHERE id = ?", (child_id,)
        ).fetchone()


def create_child(name: str, weekly_allowance_budget: float = 0.0) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO children (name, weekly_allowance_budget) VALUES (?, ?)",
            (name, weekly_allowance_budget),
        )
        return cur.lastrowid


def update_child(child_id: int, name: str, weekly_allowance_budget: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE children SET name = ?, weekly_allowance_budget = ? WHERE id = ?",
            (name, weekly_allowance_budget, child_id),
        )


def delete_child(child_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM children WHERE id = ?", (child_id,))
