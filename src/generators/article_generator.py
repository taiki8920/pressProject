"""Article generator: render markdown and html from person data and activities."""
"""Article generator: render markdown and html from person data and activities.

This module attempts to use Jinja2 and markdown if available but falls back to
minimal built-in formatting when they are not installed (so CI / quick-runs
without full deps still work).
"""
from typing import List, Dict, Optional
import html

try:
  from jinja2 import Template
  _HAS_JINJA = True
except Exception:
  Template = None  # type: ignore
  _HAS_JINJA = False

try:
  from markdown import markdown as _md_to_html
  _HAS_MARKDOWN = True
except Exception:
  _md_to_html = None  # type: ignore
  _HAS_MARKDOWN = False

DEFAULT_TEMPLATE = """# {{ name }}

{{ summary }}

## Recent activities
{% for a in activities %}
- **{{ a.title }}** — {{ a.published }}  
  {{ a.content }}
{% endfor %}
"""


def generate_article_markdown(name: str, summary: str, activities: List[Dict]) -> str:
  """Return markdown text for a person. Uses Jinja2 when available."""
  if _HAS_JINJA and Template is not None:
    tpl = Template(DEFAULT_TEMPLATE)
    return tpl.render(name=name, summary=summary or "", activities=activities)

  # Fallback: naive formatting
  lines = [f"# {name}", "", summary or "", "", "## Recent activities"]
  for a in activities:
    title = a.get("title") or "(no title)"
    published = a.get("published") or ""
    content = a.get("content") or ""
    lines.append(f"- **{title}** — {published}  \n  {content}")
  return "\n".join(lines)


def generate_article_markdown_and_log(name: str, summary: str, activities: List[Dict], person_id: Optional[int] = None, prompt: Optional[str] = None) -> str:
  """Generate markdown and optionally log generation result to DB using repository.insert_llm_log.

  This wraps `generate_article_markdown` and will not raise if DB logging fails.
  """
  md = generate_article_markdown(name, summary, activities)
  if person_id is not None:
    try:
      from src.db import repository as repo

      try:
        repo.insert_llm_log(person_id, "article_generation", None, prompt or "", md)
      except Exception:
        # swallow logging errors
        pass
    except Exception:
      pass
  return md


def generate_article_html(markdown_text: str) -> str:
  """Convert markdown text to a minimal HTML page.

  If the `markdown` package is available it will be used, otherwise a very
  small escape-and-wrap fallback is returned.
  """
  if _HAS_MARKDOWN and _md_to_html is not None:
    body = _md_to_html(markdown_text)
  else:
    # Very small fallback: escape and convert newlines to <p>
    escaped = html.escape(markdown_text)
    paragraphs = [f"<p>{p.strip()}</p>" for p in escaped.split("\n\n") if p.strip()]
    body = "\n".join(paragraphs)
  return f"<html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Article</title></head><body>{body}</body></html>"
