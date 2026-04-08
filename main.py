"""CLI entry point for social-tracker."""

import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOT_DIR = BASE_DIR / "screenshots"


def run() -> None:
    """Execute the full pipeline: screenshot, extract, store, notify."""
    raise NotImplementedError


def main() -> None:
    """Parse CLI arguments and dispatch."""
    parser = argparse.ArgumentParser(description="Track social media follower counts.")
    parser.add_argument("--no-notify", action="store_true", help="Skip sending the email report.")
    args = parser.parse_args()
    run()


if __name__ == "__main__":
    main()
