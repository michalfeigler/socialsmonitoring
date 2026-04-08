"""Claude API vision extraction: send screenshots and parse follower counts."""

from pathlib import Path


def extract_metrics(screenshot_path: Path, platform_name: str, selector_hint: str) -> dict:
    """Send a screenshot to Claude's vision API and extract follower/subscriber counts.

    Args:
        screenshot_path: Path to the PNG screenshot.
        platform_name: Name of the platform (e.g. "YouTube").
        selector_hint: What metric to look for (e.g. "subscribers").

    Returns:
        Dict with extracted metric names and their numeric values.
    """
    raise NotImplementedError


def extract_all(screenshots: list[dict]) -> list[dict]:
    """Run extraction for every screenshot in the list.

    Args:
        screenshots: List of dicts containing platform info and screenshot paths.

    Returns:
        List of dicts with platform name, timestamp, and extracted metrics.
    """
    raise NotImplementedError
