"""Playwright screenshot logic for capturing social media pages."""

import os
import random
import time
from datetime import date

from playwright.sync_api import sync_playwright

from config import PLATFORMS

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _proxy_settings() -> dict | None:
    """Build Playwright proxy settings from environment variables."""
    server = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") \
        or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    if not server:
        return None
    # Playwright expects {server, username, password} — parse user:pass@host from URL
    # Format: http://user:pass@host:port
    from urllib.parse import urlparse
    parsed = urlparse(server)
    settings = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        settings["username"] = parsed.username
    if parsed.password:
        settings["password"] = parsed.password
    return settings


def take_screenshot(url: str, platform_name: str, output_dir: str = "screenshots", page=None) -> str:
    """Navigate to *url* using Playwright and save a full-page screenshot.

    Args:
        url: The page URL to capture.
        platform_name: Used in the output filename.
        output_dir: Directory to save screenshots into.
        page: An existing Playwright page to reuse. If None, a temporary
              browser is launched and closed automatically.

    Returns:
        The file path of the saved screenshot.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{platform_name}_{date.today().isoformat()}.png"
    filepath = os.path.join(output_dir, filename)

    owns_browser = page is None
    pw_context = None
    browser = None

    try:
        if owns_browser:
            pw_context = sync_playwright().start()
            launch_kwargs = {"headless": True}
            proxy = _proxy_settings()
            if proxy:
                launch_kwargs["proxy"] = proxy
                launch_kwargs.setdefault("args", []).append("--ignore-certificate-errors")
            browser = pw_context.chromium.launch(**launch_kwargs)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=USER_AGENT,
            )
            page = context.new_page()

        # Instagram login-wall workaround: try the public JSON endpoint first
        if platform_name.lower() == "instagram":
            try:
                page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                time.sleep(3)
                # If we landed on a login page, retry with ?__a=1
                if "/accounts/login" in page.url:
                    page.goto(url + "?__a=1", timeout=30_000, wait_until="domcontentloaded")
                    time.sleep(3)
            except Exception:
                # Fall through – save whatever rendered
                pass
        else:
            try:
                page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            except Exception:
                # Timeout or navigation error – save whatever rendered
                pass

        # Extra wait for JS-heavy pages
        time.sleep(5)

        page.screenshot(path=filepath, full_page=True)

    except Exception:
        # Last resort: if screenshot itself fails, try a viewport-only shot
        try:
            page.screenshot(path=filepath)
        except Exception:
            pass

    finally:
        if owns_browser:
            if browser:
                browser.close()
            if pw_context:
                pw_context.stop()

    return filepath


def take_all_screenshots(platforms: list | None = None) -> dict:
    """Take screenshots for every platform, reusing one browser instance.

    Args:
        platforms: List of platform dicts (name, url, selector_hint).
                   Defaults to config.PLATFORMS.

    Returns:
        Dict mapping platform name to the screenshot file path.
    """
    if platforms is None:
        platforms = PLATFORMS

    results = {}

    pw = sync_playwright().start()
    launch_kwargs = {"headless": True}
    proxy = _proxy_settings()
    if proxy:
        launch_kwargs["proxy"] = proxy
        launch_kwargs.setdefault("args", []).append("--ignore-certificate-errors")
    browser = pw.chromium.launch(**launch_kwargs)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=USER_AGENT,
    )

    try:
        for i, platform in enumerate(platforms):
            name = platform["name"]
            url = platform["url"]
            page = context.new_page()

            try:
                path = take_screenshot(url, name, page=page)
                results[name] = path
                print(f"[+] {name}: {path}")
            except Exception as exc:
                print(f"[!] {name}: failed – {exc}")
                results[name] = None
            finally:
                page.close()

            # Random delay between platforms to look less bot-like
            if i < len(platforms) - 1:
                delay = random.uniform(2, 4)
                time.sleep(delay)
    finally:
        browser.close()
        pw.stop()

    return results


if __name__ == "__main__":
    screenshots = take_all_screenshots()
    print("\n--- Results ---")
    for name, path in screenshots.items():
        print(f"  {name}: {path}")
