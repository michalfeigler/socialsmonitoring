"""SQLite storage and delta calculation for tracked metrics."""

import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "tracker.db")

CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS follower_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    date TEXT NOT NULL,
    count INTEGER,
    raw_text TEXT,
    confidence TEXT,
    notes TEXT,
    screenshot_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(platform, date)
);
"""


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    """Return a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    """Create the follower_counts table if it doesn't exist."""
    os.makedirs(os.path.dirname(db_path or DB_PATH), exist_ok=True)
    conn = _connect(db_path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


def save_count(
    platform: str,
    date: str,
    count: int | None,
    raw_text: str | None,
    confidence: str | None,
    notes: str | None,
    screenshot_path: str | None,
    db_path: str | None = None,
) -> None:
    """Upsert a follower count row for a platform + date."""
    conn = _connect(db_path)
    conn.execute(
        """\
        INSERT OR REPLACE INTO follower_counts
            (platform, date, count, raw_text, confidence, notes, screenshot_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (platform, date, count, raw_text, confidence, notes, screenshot_path),
    )
    conn.commit()
    conn.close()


def get_latest_counts(date: str, db_path: str | None = None) -> list[dict]:
    """Get all platform counts for a given date."""
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM follower_counts WHERE date = ? ORDER BY platform",
        (date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_previous_counts(date: str, db_path: str | None = None) -> list[dict]:
    """Get all platform counts for the day before *date*."""
    prev = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    return get_latest_counts(prev, db_path)


def get_daily_report(date: str, db_path: str | None = None) -> list[dict]:
    """Build a comparison report between *date* and the previous day.

    Returns a sorted list of dicts with:
        platform, today_count, yesterday_count, change_absolute,
        change_percent, confidence, notes
    """
    today_rows = {r["platform"]: r for r in get_latest_counts(date, db_path)}
    yesterday_rows = {r["platform"]: r for r in get_previous_counts(date, db_path)}

    platforms = sorted(set(today_rows) | set(yesterday_rows))
    report = []

    for name in platforms:
        today = today_rows.get(name, {})
        yesterday = yesterday_rows.get(name, {})

        today_count = today.get("count")
        yesterday_count = yesterday.get("count")

        if today_count is not None and yesterday_count is not None:
            change_abs = today_count - yesterday_count
            change_pct = round(change_abs / yesterday_count * 100, 1) if yesterday_count else None
        else:
            change_abs = None
            change_pct = None

        report.append({
            "platform": name,
            "today_count": today_count,
            "yesterday_count": yesterday_count,
            "change_absolute": change_abs,
            "change_percent": change_pct,
            "confidence": today.get("confidence"),
            "notes": today.get("notes"),
        })

    return report


def get_history(platform: str, days: int = 30, db_path: str | None = None) -> list[dict]:
    """Return the last *days* entries for a platform, newest first."""
    conn = _connect(db_path)
    rows = conn.execute(
        """\
        SELECT * FROM follower_counts
        WHERE platform = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (platform, days),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    import tempfile

    db = os.path.join(tempfile.mkdtemp(), "test_tracker.db")
    print(f"Using temp DB: {db}")

    init_db(db)

    # Insert sample data for two days
    for platform, y_count, t_count in [
        ("Facebook", 1200, 1250),
        ("Instagram", 5400, 5500),
        ("LinkedIn", 800, 810),
        ("Spotify", 3200, 3300),
        ("TikTok", 15000, 15400),
        ("Threads", 900, 920),
        ("X", 2100, 2100),
        ("YouTube", 10500, 10750),
    ]:
        save_count(platform, "2026-04-07", y_count, f"{y_count} followers", "high", None, None, db)
        save_count(platform, "2026-04-08", t_count, f"{t_count} followers", "high", None, None, db)

    # Print daily report
    report = get_daily_report("2026-04-08", db)
    print(f"\n{'Platform':<12} {'Today':>8} {'Yesterday':>10} {'Change':>8} {'%':>7}")
    print("-" * 50)
    for r in report:
        t = r["today_count"] or "N/A"
        y = r["yesterday_count"] or "N/A"
        c = r["change_absolute"] if r["change_absolute"] is not None else "N/A"
        p = f"{r['change_percent']}%" if r["change_percent"] is not None else "N/A"
        print(f"{r['platform']:<12} {t:>8} {y:>10} {c:>8} {p:>7}")

    # Print history for one platform
    print("\nYouTube history:")
    for row in get_history("YouTube", db_path=db):
        print(f"  {row['date']}: {row['count']}")
