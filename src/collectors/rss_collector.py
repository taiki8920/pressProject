"""Simple RSS/Atom feed parser using feedparser."""
import feedparser
from typing import List, Dict


def parse_rss_feed(url: str) -> List[Dict]:
    """Fetch RSS/Atom feed and return list of entries as dicts."""
    feed = feedparser.parse(url)
    entries = []
    for e in getattr(feed, "entries", []):
        entries.append({
            "title": e.get("title"),
            "link": e.get("link"),
            "published": e.get("published"),
            "summary": e.get("summary", ""),
        })
    return entries
