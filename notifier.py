"""SMTP email sender for daily metric reports."""

import argparse
import glob
import os
import smtplib
import zipfile
from email.message import EmailMessage

from config import EMAIL_FROM, EMAIL_TO, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def _build_html(report_data: list, date: str) -> str:
    """Build the HTML body for the daily report email."""
    rows_html = ""
    for r in report_data:
        count_cell = _format_count(r)
        change_cell, pct_cell = _format_change(r)
        conf = r.get("confidence") or "—"

        rows_html += (
            "<tr>"
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee">{r["platform"]}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">{count_cell}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">{change_cell}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right">{pct_cell}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:center">{conf}</td>'
            "</tr>\n"
        )

    return f"""\
<html>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f4f4f4">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:24px 0">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden">

  <tr><td style="background:#1a1a2e;color:#fff;padding:24px 32px">
    <h1 style="margin:0;font-size:22px">Taking Over &mdash; Daily Follower Report</h1>
    <p style="margin:6px 0 0;font-size:14px;color:#ccc">{date}</p>
  </td></tr>

  <tr><td style="padding:24px 32px">
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px">
      <tr style="background:#f8f8f8">
        <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #ddd">Platform</th>
        <th style="padding:10px 12px;text-align:right;border-bottom:2px solid #ddd">Followers</th>
        <th style="padding:10px 12px;text-align:right;border-bottom:2px solid #ddd">Change</th>
        <th style="padding:10px 12px;text-align:right;border-bottom:2px solid #ddd">% Change</th>
        <th style="padding:10px 12px;text-align:center;border-bottom:2px solid #ddd">Confidence</th>
      </tr>
      {rows_html}
    </table>
  </td></tr>

  <tr><td style="padding:16px 32px 24px;font-size:12px;color:#999;border-top:1px solid #eee">
    Automated report &mdash; Taking Over Podcast Social Tracker
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def _build_empty_html(date: str) -> str:
    """HTML body when no data was collected."""
    return f"""\
<html>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background:#f4f4f4">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:24px 0">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden">
  <tr><td style="background:#1a1a2e;color:#fff;padding:24px 32px">
    <h1 style="margin:0;font-size:22px">Taking Over &mdash; Daily Follower Report</h1>
    <p style="margin:6px 0 0;font-size:14px;color:#ccc">{date}</p>
  </td></tr>
  <tr><td style="padding:32px;text-align:center;color:#c0392b;font-size:16px">
    <strong>No data collected today &mdash; check logs.</strong>
  </td></tr>
  <tr><td style="padding:16px 32px 24px;font-size:12px;color:#999;border-top:1px solid #eee">
    Automated report &mdash; Taking Over Podcast Social Tracker
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _format_count(row: dict) -> str:
    """Format the follower count cell."""
    count = row.get("today_count")
    if count is None:
        notes = row.get("notes") or "no data"
        return f'<span style="color:#999">N/A</span> <span style="color:#bbb;font-size:12px">({notes})</span>'
    return f"{count:,}"


def _format_change(row: dict) -> tuple[str, str]:
    """Return (change_cell, percent_cell) HTML strings."""
    change = row.get("change_absolute")
    pct = row.get("change_percent")

    if change is None:
        gray = '<span style="color:#999">&mdash;</span>'
        return gray, gray

    if change > 0:
        color = "#27ae60"
        arrow = "&uarr;"
        sign = "+"
    elif change < 0:
        color = "#c0392b"
        arrow = "&darr;"
        sign = ""
    else:
        return (
            '<span style="color:#999">&mdash;</span>',
            '<span style="color:#999">0.0%</span>',
        )

    change_html = f'<span style="color:{color}">{arrow} {sign}{change:,}</span>'
    pct_html = f'<span style="color:{color}">{sign}{pct}%</span>' if pct is not None else '<span style="color:#999">&mdash;</span>'
    return change_html, pct_html


def _zip_screenshots(date: str, screenshots_dir: str) -> str | None:
    """Create a ZIP of today's screenshots. Returns path or None."""
    pattern = os.path.join(screenshots_dir, f"*_{date}.png")
    files = glob.glob(pattern)
    if not files:
        return None

    zip_path = os.path.join(screenshots_dir, f"screenshots_{date}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, os.path.basename(f))
    return zip_path


def _send(subject: str, html_body: str, attachment_path: str | None = None) -> None:
    """Send an HTML email, optionally with a ZIP attachment."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content("Please view this email in an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="zip",
                filename=os.path.basename(attachment_path),
            )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_daily_report(report_data: list, date: str, screenshots_dir: str = "screenshots") -> None:
    """Send the daily follower report as an HTML email with screenshot ZIP.

    Args:
        report_data: List of dicts from db.get_daily_report().
        date: Report date as YYYY-MM-DD.
        screenshots_dir: Directory containing screenshot PNGs.
    """
    subject = f"Taking Over - Follower Report - {date}"

    if not report_data:
        html = _build_empty_html(date)
        _send(subject, html)
        print(f"[email] Sent empty-data notice for {date}")
        return

    html = _build_html(report_data, date)
    zip_path = _zip_screenshots(date, screenshots_dir)
    _send(subject, html, zip_path)

    att = f" + {os.path.basename(zip_path)}" if zip_path else ""
    print(f"[email] Sent report for {date}{att}")


def send_test_email() -> None:
    """Send a test email with dummy data to verify SMTP works."""
    dummy = [
        {"platform": "YouTube", "today_count": 10750, "yesterday_count": 10500,
         "change_absolute": 250, "change_percent": 2.4, "confidence": "high", "notes": None},
        {"platform": "Instagram", "today_count": 5500, "yesterday_count": 5400,
         "change_absolute": 100, "change_percent": 1.9, "confidence": "high", "notes": None},
        {"platform": "TikTok", "today_count": None, "yesterday_count": 15000,
         "change_absolute": None, "change_percent": None, "confidence": None, "notes": "login wall detected"},
        {"platform": "X", "today_count": 2100, "yesterday_count": 2100,
         "change_absolute": 0, "change_percent": 0.0, "confidence": "medium", "notes": None},
    ]
    subject = "Taking Over - Test Email"
    html = _build_html(dummy, "2026-01-01")
    _send(subject, html)
    print("[email] Test email sent successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notifier test utility")
    parser.add_argument("--test", action="store_true", help="Send a test email")
    args = parser.parse_args()

    if args.test:
        send_test_email()
    else:
        parser.print_help()
