"""Playwright screenshot logic for capturing social media pages."""

from pathlib import Path


async def take_screenshot(url: str, output_path: Path) -> Path:
    """Navigate to *url* using Playwright and save a full-page screenshot.

    Args:
        url: The page URL to capture.
        output_path: File path where the PNG screenshot will be saved.

    Returns:
        The path to the saved screenshot.
    """
    raise NotImplementedError


async def capture_all_platforms(platforms: list[dict], screenshot_dir: Path) -> list[dict]:
    """Take screenshots for every platform in the list.

    Args:
        platforms: List of platform dicts (name, url, selector_hint).
        screenshot_dir: Directory to store screenshot files.

    Returns:
        List of dicts with platform info and the path to each screenshot.
    """
    raise NotImplementedError
