"""SQLite storage and delta calculation for tracked metrics."""

from pathlib import Path


def init_db(db_path: Path) -> None:
    """Create the SQLite database and tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file.
    """
    raise NotImplementedError


def store_metrics(db_path: Path, metrics: list[dict]) -> None:
    """Insert a batch of extracted metrics into the database.

    Args:
        db_path: Path to the SQLite database file.
        metrics: List of metric dicts (platform, metric_name, value, timestamp).
    """
    raise NotImplementedError


def calculate_deltas(db_path: Path) -> list[dict]:
    """Compare the latest metrics with the previous run and return deltas.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of dicts with platform, metric, current value, previous value, and delta.
    """
    raise NotImplementedError
