# Family Chores

A household chores management app for kids, built with Python and Streamlit. Parents can create and manage chores with allowance rewards; children can view their schedule, mark chores done, and watch their earnings grow.

## Features

- **Two roles** — Parent (PIN-protected) and Child, selectable from the sidebar
- **Calendar views** — Week view and Day view showing every chore's status at a glance
- **Recurring chores** — Daily (specific days of week), weekly, or one-time
- **Two allowance types per chore:**
  - 💰 **Monetary** — fixed dollar amount, or a weighted share of a weekly budget
  - 🎮 **Screen time** — minutes earned, banked for use the next day
- **Approval flow** — child marks a chore done → parent approves → wallet is credited
- **Missed chores** — past-due uncompleted chores are automatically marked missed
- **Multiple children** — each child has their own chores, schedule, and wallet
- **Local SQLite database** — no cloud account or internet connection required

## Setup

**Requirements:** Python 3.9+

```bash
pip install streamlit
```

## Running the App

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`. The SQLite database (`chores.db`) is created automatically on first run.

## Default Login

| Role   | Credential       |
|--------|------------------|
| Parent | PIN: **1234**    |
| Child  | No PIN — select name from sidebar |

Change the parent PIN any time under **Parent → Settings**.

## How It Works

### Parent view
1. Go to **Children** tab → add each child and set their weekly allowance budget
2. Go to **Chores** tab → add chores, assign them to a child, set recurrence and allowance
3. Check the **Approvals** tab daily to approve completed chores
4. At the end of the week, click **Finalize Week** in the Children tab to distribute weighted allowances

### Child view
1. Select your name from the sidebar
2. Use **Week View** to see the whole week, **Day View** to see today's chores
3. Click **Mark Done** when you finish a chore — it turns yellow until a parent approves
4. Click **Undo** if you marked a chore done by mistake
5. Your money earned and screen time banked are shown at the top

### Allowance types

| Type | How it works |
|------|-------------|
| Fixed | Child earns the exact dollar amount set on the chore, credited immediately on approval |
| Weighted | Each chore has a weight; at week's end, payout = `(weight ÷ total weights) × weekly budget`. Parent clicks **Finalize Week** to distribute |
| Screen time | Minutes earned, credited immediately on approval, visible in the child's wallet |
| Both | Fixed dollars + weighted share — fixed is credited immediately, weighted at week-end |

### Chore status flow

```
pending → (child marks done) → completed_pending_approval → (parent approves) → approved
                                        ↓
                              (child clicks Undo)
                                     pending
```

Past-due chores that were never completed are swept to **missed** on the next app load.

## Project Structure

```
chores/
├── app.py                    # Entry point — initialises DB, routes to parent/child UI
├── requirements.txt
├── db/
│   ├── connection.py         # SQLite context manager
│   ├── schema.py             # CREATE TABLE statements + default PIN seed
│   └── queries/
│       ├── children.py       # Child CRUD
│       ├── chores.py         # Chore template CRUD
│       ├── chore_instances.py # Per-day instances, status transitions, missed sweep
│       ├── settings.py       # Key/value settings (PIN hash)
│       └── wallets.py        # Append-only ledger, balance reads
├── logic/
│   ├── auth.py               # PIN hashing and session helpers
│   ├── recurrence.py         # Expands chore templates into daily instances
│   ├── allowance.py          # Fixed and weighted payout calculations
│   └── wallet.py             # Orchestrates status transitions + wallet credits
└── ui/
    ├── auth_gate.py          # Sidebar role selector and PIN entry
    ├── parent/
    │   ├── dashboard.py      # Approval queue
    │   ├── chore_manager.py  # Add / edit / delete chore templates
    │   ├── child_manager.py  # Manage children, wallets, weekly finalization
    │   └── settings.py       # Change PIN
    └── child/
        ├── dashboard.py      # Wallet summary + calendar
        ├── calendar.py       # Week view and Day view
        └── chore_add.py      # Child-facing add-chore form
```

## Data Storage

All data is stored locally in `chores.db` (SQLite). The file is created automatically and excluded from version control via `.gitignore`. Back it up to preserve your family's chore history.
