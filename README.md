# social-tracker

Track social media follower and subscriber counts across multiple platforms using Playwright screenshots and Claude vision extraction.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # fill in your secrets
```

## Usage

```bash
python main.py              # run full pipeline
python main.py --no-notify  # skip email report
```

## Tracked Platforms

YouTube, TikTok, Spotify, Instagram, Threads, Facebook, LinkedIn, X
