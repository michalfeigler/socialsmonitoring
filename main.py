"""CLI entry point for social-tracker."""

import argparse
import sys
import time
from datetime import date, datetime

from config import PLATFORMS
from db import get_daily_report, get_history, init_db, save_count
from extractor import extract_all_counts
from notifier import send_daily_report, send_test_email
from screenshot import take_all_screenshots

SCREENSHOTS_DIR = "screenshots"


def _today() -> str:
    return date.today().isoformat()


def _print_report(report: list, report_date: str) -> None:
    """Pretty-print a daily report to the console."""
    print(f"\n  Daily Report — {report_date}")
    print(f"  {'Platform':<12} {'Followers':>10} {'Change':>8} {'%':>7}  {'Conf':<6}  Notes")
    print("  " + "-" * 70)
    for r in report:
        cnt = f"{r['today_count']:,}" if r["today_count"] is not None else "N/A"
        if r["change_absolute"] is not None and r["change_absolute"] != 0:
            sign = "+" if r["change_absolute"] > 0 else ""
            chg = f"{sign}{r['change_absolute']:,}"
        elif r["change_absolute"] == 0:
            chg = "—"
        else:
            chg = "—"
        pct = f"{r['change_percent']}%" if r["change_percent"] is not None else "—"
        conf = r.get("confidence") or "—"
        notes = r.get("notes") or ""
        print(f"  {r['platform']:<12} {cnt:>10} {chg:>8} {pct:>7}  {conf:<6}  {notes}")
    print()


def cmd_run(args: argparse.Namespace) -> None:
    """Full daily pipeline: screenshot -> extract -> save -> email."""
    report_date = args.date or _today()
    start = time.time()
    print(f"[run] Starting at {datetime.now().strftime('%H:%M:%S')}  date={report_date}")

    # 1. Init DB
    if args.verbose:
        print("[run] Initializing database...")
    init_db()

    # 2. Screenshots
    print("[run] Taking screenshots...")
    screenshots = take_all_screenshots(PLATFORMS)

    # 3. Extract
    print("[run] Extracting follower counts...")
    results = extract_all_counts(screenshots, PLATFORMS)

    # 4. Save to DB
    if args.verbose:
        print("[run] Saving to database...")
    for r in results:
        save_count(
            platform=r["platform"],
            date=report_date,
            count=r.get("count"),
            raw_text=r.get("raw_text"),
            confidence=r.get("confidence"),
            notes=r.get("notes"),
            screenshot_path=screenshots.get(r["platform"]),
        )

    # 5. Generate report
    report = get_daily_report(report_date)
    _print_report(report, report_date)

    # 6. Email
    if not args.no_email:
        print("[run] Sending email report...")
        send_daily_report(report, report_date, SCREENSHOTS_DIR)
    else:
        print("[run] Skipping email (--no-email)")

    elapsed = time.time() - start
    print(f"[run] Done at {datetime.now().strftime('%H:%M:%S')}  ({elapsed:.1f}s)")


def cmd_screenshots(args: argparse.Namespace) -> None:
    """Take screenshots only."""
    print("[screenshots] Capturing all platforms...")
    screenshots = take_all_screenshots(PLATFORMS)
    print(f"\n  Saved {sum(1 for v in screenshots.values() if v)} / {len(screenshots)} screenshots")


def cmd_extract(args: argparse.Namespace) -> None:
    """Extract counts from today's existing screenshots."""
    report_date = args.date or _today()
    init_db()

    # Build screenshots dict from existing files on disk
    import os
    screenshots = {}
    for p in PLATFORMS:
        path = os.path.join(SCREENSHOTS_DIR, f"{p['name']}_{report_date}.png")
        screenshots[p["name"]] = path if os.path.exists(path) else None

    found = sum(1 for v in screenshots.values() if v)
    if not found:
        print(f"[extract] No screenshots found for {report_date}")
        return

    print(f"[extract] Found {found} screenshots for {report_date}")
    results = extract_all_counts(screenshots, PLATFORMS)

    for r in results:
        save_count(
            platform=r["platform"],
            date=report_date,
            count=r.get("count"),
            raw_text=r.get("raw_text"),
            confidence=r.get("confidence"),
            notes=r.get("notes"),
            screenshot_path=screenshots.get(r["platform"]),
        )
    print(f"[extract] Saved {len(results)} results to DB")


def cmd_report(args: argparse.Namespace) -> None:
    """Print today's report to console (no email)."""
    report_date = args.date or _today()
    init_db()
    report = get_daily_report(report_date)
    if not report:
        print(f"[report] No data for {report_date}")
        return
    _print_report(report, report_date)


def cmd_test_email(args: argparse.Namespace) -> None:
    """Send test email."""
    print("[test-email] Sending...")
    send_test_email()


def cmd_history(args: argparse.Namespace) -> None:
    """Print last 7 days for all platforms."""
    init_db()
    for p in PLATFORMS:
        rows = get_history(p["name"], days=7)
        print(f"\n  {p['name']}")
        if not rows:
            print("    (no data)")
            continue
        for row in rows:
            cnt = f"{row['count']:,}" if row["count"] is not None else "N/A"
            print(f"    {row['date']}  {cnt}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Taking Over — Social Media Follower Tracker",
    )
    parser.add_argument("--date", help="Override date (YYYY-MM-DD), default today")
    parser.add_argument("--no-email", action="store_true", help="Skip sending email")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    sub = parser.add_subparsers(dest="command")

    for name, helptext in [
        ("run", "Full daily pipeline"),
        ("screenshots", "Take screenshots only"),
        ("extract", "Extract from today's screenshots"),
        ("report", "Print today's report (no email)"),
        ("test-email", "Send a test email"),
        ("history", "Last 7 days for all platforms"),
    ]:
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("--date", help="Override date (YYYY-MM-DD), default today")
        sp.add_argument("--no-email", action="store_true", help="Skip sending email")
        sp.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    commands = {
        "run": cmd_run,
        "screenshots": cmd_screenshots,
        "extract": cmd_extract,
        "report": cmd_report,
        "test-email": cmd_test_email,
        "history": cmd_history,
    }

    handler = commands.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)

    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as exc:
        print(f"\n[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
