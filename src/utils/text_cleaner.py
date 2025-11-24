"""Small utilities to clean HTML/text pulled from feeds/pages."""
import re


def clean_html_to_text(html: str) -> str:
    """Very small HTML to text cleaner for feed/content."""
    text = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
