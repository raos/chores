import hashlib
from db.connection import get_connection

_DDL = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS children (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT    NOT NULL,
    weekly_allowance_budget REAL    NOT NULL DEFAULT 0.0,
    created_at              TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chores (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT NOT NULL,
    description       TEXT,
    assigned_to       INTEGER REFERENCES children(id) ON DELETE SET NULL,
    created_by_role   TEXT NOT NULL CHECK(created_by_role IN ('parent','child')),
    recurrence_type   TEXT NOT NULL CHECK(recurrence_type IN ('once','daily','weekly')),
    recurrence_days   TEXT,
    start_date        TEXT NOT NULL,
    end_date          TEXT,
    allowance_type    TEXT CHECK(allowance_type IN ('fixed','weighted','both',NULL)),
    fixed_amount      REAL,
    chore_weight      REAL,
    screen_time_hours REAL DEFAULT 0.0,
    is_active         INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chore_instances (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    chore_id       INTEGER NOT NULL REFERENCES chores(id) ON DELETE CASCADE,
    scheduled_date TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'pending'
                   CHECK(status IN ('pending','completed_pending_approval','approved','missed')),
    completed_at   TEXT,
    approved_at    TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chore_id, scheduled_date)
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id          INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    chore_instance_id INTEGER REFERENCES chore_instances(id),
    transaction_type  TEXT NOT NULL CHECK(transaction_type IN ('monetary','screen_time')),
    amount            REAL NOT NULL,
    note              TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(chore_instance_id, transaction_type)
);

CREATE TABLE IF NOT EXISTS weekly_allowance_snapshots (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id         INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    week_start_date  TEXT    NOT NULL,
    total_payout     REAL    NOT NULL,
    calculation_json TEXT,
    finalized_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(child_id, week_start_date)
);
"""


def initialize_db():
    with get_connection() as conn:
        conn.executescript(_DDL)


def seed_defaults():
    default_pin_hash = hashlib.sha256(b"1234").hexdigest()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('pin_hash', ?)",
            (default_pin_hash,),
        )
