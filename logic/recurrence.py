import json
from datetime import date, timedelta
from db.queries.chores import list_chores
from db.queries.chore_instances import upsert_instances


def expand_chore(chore, window_start: date, window_end: date) -> list[dict]:
    rows = []
    rec_type = chore["recurrence_type"]
    chore_start = date.fromisoformat(chore["start_date"])
    chore_end = date.fromisoformat(chore["end_date"]) if chore["end_date"] else None

    effective_start = max(chore_start, window_start)
    effective_end = min(chore_end, window_end) if chore_end else window_end

    if effective_start > effective_end:
        return rows

    if rec_type == "once":
        d = chore_start
        if window_start <= d <= window_end:
            rows.append({"chore_id": chore["id"], "scheduled_date": d.isoformat()})

    elif rec_type in ("daily", "weekly"):
        raw_days = chore["recurrence_days"]
        if not raw_days:
            return rows
        allowed_days = set(json.loads(raw_days))
        current = effective_start
        while current <= effective_end:
            if current.weekday() in allowed_days:
                rows.append({
                    "chore_id": chore["id"],
                    "scheduled_date": current.isoformat(),
                })
            current += timedelta(days=1)

    return rows


def ensure_instances_for_window(window_start: date, window_end: date) -> None:
    chores = list_chores(active_only=True)
    all_rows = []
    for chore in chores:
        all_rows.extend(expand_chore(chore, window_start, window_end))
    upsert_instances(all_rows)
