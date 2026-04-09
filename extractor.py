"""Claude API vision extraction: send screenshots and parse follower counts."""

import base64
import json
import sys

import anthropic

from config import ANTHROPIC_API_KEY, PLATFORMS

PROMPT_TEMPLATE = (
    "Look at this screenshot of a {platform_name} profile page. "
    "Find and extract the follower/subscriber count. "
    "The relevant metric is: {selector_hint}.\n\n"
    "Return ONLY a JSON object with these fields:\n"
    '- count: the number as an integer (e.g. 1500, not "1.5K"). '
    "Convert K to thousands, M to millions. If you cannot find the count, return null.\n"
    '- raw_text: the exact text you see on the page for this metric (e.g. "1.5K followers")\n'
    '- confidence: "high", "medium", or "low"\n'
    '- notes: any issues (e.g. "login wall detected", "page didn\'t load", "count not visible")\n\n'
    "Return ONLY the JSON, no other text."
)


def extract_follower_count(screenshot_path: str, platform_name: str, selector_hint: str) -> dict:
    """Send a screenshot to Claude's vision API and extract follower/subscriber counts.

    Args:
        screenshot_path: Path to the PNG screenshot file.
        platform_name: Name of the platform (e.g. "YouTube").
        selector_hint: What metric to look for (e.g. "subscribers").

    Returns:
        Dict with count, raw_text, confidence, notes, and platform fields.
    """
    result = {
        "platform": platform_name,
        "count": None,
        "raw_text": None,
        "confidence": "low",
        "notes": None,
    }

    # Read and encode the screenshot
    try:
        with open(screenshot_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        result["notes"] = f"Screenshot not found: {screenshot_path}"
        return result
    except Exception as exc:
        result["notes"] = f"Failed to read screenshot: {exc}"
        return result

    # Call the Anthropic API
    prompt = PROMPT_TEMPLATE.format(
        platform_name=platform_name,
        selector_hint=selector_hint,
    )

    try:
        client_kwargs = {}
        if ANTHROPIC_API_KEY:
            client_kwargs["api_key"] = ANTHROPIC_API_KEY
        client = anthropic.Anthropic(**client_kwargs)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
    except Exception as exc:
        result["notes"] = f"API call failed: {exc}"
        return result

    # Parse the JSON response
    raw_response = message.content[0].text.strip()

    try:
        # Strip markdown fences if the model wraps the JSON
        cleaned = raw_response
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)
        result["count"] = parsed.get("count")
        result["raw_text"] = parsed.get("raw_text")
        result["confidence"] = parsed.get("confidence", "low")
        result["notes"] = parsed.get("notes")
    except (json.JSONDecodeError, IndexError, AttributeError) as exc:
        result["notes"] = f"Failed to parse response: {exc}. Raw: {raw_response[:200]}"

    return result


def extract_all_counts(screenshots: dict, platforms: list | None = None) -> list:
    """Run extraction for every platform screenshot.

    Args:
        screenshots: Dict mapping platform name to screenshot file path
                     (as returned by screenshot.take_all_screenshots).
        platforms: List of platform dicts (name, url, selector_hint).
                   Defaults to config.PLATFORMS.

    Returns:
        List of result dicts, one per platform.
    """
    if platforms is None:
        platforms = PLATFORMS

    hint_map = {p["name"]: p["selector_hint"] for p in platforms}
    results = []

    for platform_name, path in screenshots.items():
        if path is None:
            results.append({
                "platform": platform_name,
                "count": None,
                "raw_text": None,
                "confidence": "low",
                "notes": "No screenshot available",
            })
            continue

        hint = hint_map.get(platform_name, "followers")
        result = extract_follower_count(path, platform_name, hint)
        results.append(result)
        print(f"  {platform_name}: count={result['count']}  confidence={result['confidence']}")

    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python extractor.py <screenshot_path> <platform_name> <selector_hint>")
        print("Example: python extractor.py screenshots/YouTube_2026-04-08.png YouTube subscribers")
        sys.exit(1)

    path, name, hint = sys.argv[1], sys.argv[2], sys.argv[3]
    result = extract_follower_count(path, name, hint)
    print(json.dumps(result, indent=2))
