"""Fetch short summary from Wikipedia REST API."""
import requests
from typing import Optional

WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"


def collect_wikipedia(name: str) -> Optional[str]:
    """Fetch a short summary from Wikipedia REST API (title-cased)."""
    title = name.replace(" ", "_")
    url = WIKI_API_URL.format(title)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("extract")
    except Exception:
        return None
    return None
