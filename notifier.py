"""SMTP email sender for daily metric reports."""


def send_email(subject: str, body: str) -> None:
    """Send an email report via SMTP using credentials from config.

    Args:
        subject: Email subject line.
        body: Plain-text email body.
    """
    raise NotImplementedError


def format_report(deltas: list[dict]) -> str:
    """Build a human-readable report from metric deltas.

    Args:
        deltas: List of delta dicts from db.calculate_deltas().

    Returns:
        Formatted plain-text report string.
    """
    raise NotImplementedError
