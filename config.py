"""Configuration: platform URLs, settings, and environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Anthropic ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- SMTP ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "mf@tackroomcapital.com")

# --- Platforms to track ---
PLATFORMS = [
    {
        "name": "YouTube",
        "url": "https://www.youtube.com/@takingoverpodcast",
        "selector_hint": "subscribers",
    },
    {
        "name": "TikTok",
        "url": "https://www.tiktok.com/@takingover.cz",
        "selector_hint": "followers",
    },
    {
        "name": "Spotify",
        "url": "https://open.spotify.com/show/5FyfP3CrsBoaj9Hx2BWwcN",
        "selector_hint": "followers or monthly listeners",
    },
    {
        "name": "Instagram",
        "url": "https://www.instagram.com/takingover.cz",
        "selector_hint": "followers",
    },
    {
        "name": "Threads",
        "url": "https://www.threads.com/@takingover.cz",
        "selector_hint": "followers",
    },
    {
        "name": "Facebook",
        "url": "https://www.facebook.com/takingover.cz",
        "selector_hint": "followers or likes",
    },
    {
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/company/takingover",
        "selector_hint": "followers",
    },
    {
        "name": "X",
        "url": "https://x.com/takingvercz",
        "selector_hint": "followers",
    },
]
