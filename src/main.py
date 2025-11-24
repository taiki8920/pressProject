"""Bootstrap and example runner for Press Project.

Usage:
    python src/main.py

This script will initialize the DB schema. It includes an example_flow that
is guarded by the SKIP_NETWORK environment variable to avoid network calls in CI.
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from src...` imports work when running
# `python src/main.py` directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db import repository as repo
from src.generators.article_generator import (
    generate_article_markdown_and_log,
    generate_article_html,
)
from src.utils.diff_util import compute_diff
import logging

logging.basicConfig(level=logging.INFO)


def slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name).strip("_")


def read_persons() -> list:
    """Attempt to read persons from data/persons.csv or data/persons.txt.

    CSV format: name,rss,x_urls  (rss and x_urls are semicolon-separated lists)
    TXT format: one name per line
    If none found, return a small default list.
    """
    persons = []
    csv_path = Path("data") / "persons.csv"
    txt_path = Path("data") / "persons.txt"
    if csv_path.exists():
        import csv

        with csv_path.open("r", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                name = r.get("name") or r.get("Name")
                if not name:
                    continue
                rss = (r.get("rss") or "")
                x_urls = (r.get("x_urls") or "")
                persons.append({"name": name.strip(), "rss": [u for u in rss.split(";") if u], "x_urls": [u for u in x_urls.split(";") if u]})
        return persons
    if txt_path.exists():
        for line in txt_path.read_text(encoding="utf-8").splitlines():
            name = line.strip()
            if name:
                persons.append({"name": name, "rss": [], "x_urls": []})
        return persons

    # fallback defaults
    return [{"name": "Sample Politician", "rss": [], "x_urls": []}]


def process_person(p: dict, skip_network: bool = False):
    name = p.get("name")
    print(f"Processing: {name}")

    # 1) Wikipedia summary
    summary = None
    if not skip_network:
        try:
            from src.collectors.wikipedia_collector import collect_wikipedia

            summary = collect_wikipedia(name)
        except Exception as e:
            print("Wikipedia fetch failed:", e)
    # upsert person record
    person_id = repo.upsert_person(name, wikipedia_summary=summary)

    # 2) Collect RSS activities
    activities = []
    if not skip_network and p.get("rss"):
        try:
            from src.collectors.rss_collector import parse_rss_feed

            for feed in p.get("rss", []):
                try:
                    entries = parse_rss_feed(feed)
                except Exception as e:
                    print(f"Failed to parse feed {feed}:", e)
                    continue
                for e in entries:
                    title = e.get("title") or ""
                    summary_text = e.get("summary") or ""
                    # naive relevance check
                    if name.lower() in (title + " " + summary_text).lower():
                        src_id = repo.insert_source(e.get("link") or feed, type_="rss")
                        aid = repo.insert_activity(person_id, title, summary_text, source_id=src_id, published_at=e.get("published"))
                        activities.append({"title": title, "content": summary_text, "published": e.get("published")})
        except Exception as e:
            print("RSS collection error:", e)

    # 3) X/Twitter URL summarization
    if not skip_network and p.get("x_urls"):
        try:
            from src.collectors.x_url_summarizer import summarize_url_with_gpt

            for url in p.get("x_urls", []):
                try:
                    s = summarize_url_with_gpt(url)
                except Exception as e:
                    print("X URL summarizer failed:", e)
                    s = None
                if s:
                    src_id = repo.insert_source(url, type_="x_url")
                    repo.insert_activity(person_id, f"X post summary", s, source_id=src_id)
                    activities.append({"title": "X post", "content": s, "published": ""})
        except Exception as e:
            print("X summarizer error:", e)

    # 4) Generate article (use wrapper that also logs to llm_logs)
    try:
        md = generate_article_markdown_and_log(
            name, summary or "", activities, person_id=person_id, prompt="auto-article-template-v1"
        )
    except Exception as e:
        logging.warning("Article generation/logging failed for %s: %s", name, e)
        # fallback to plain generator (should not raise normally)
        try:
            # fallback: try basic generator
            from src.generators.article_generator import generate_article_markdown

            md = generate_article_markdown(name, summary or "", activities)
        except Exception:
            logging.exception("Article generation completely failed for %s", name)
            md = f"# {name}\n\n{summary or ''}"

    try:
        html = generate_article_html(md)
    except Exception:
        logging.exception("HTML conversion failed for %s; using escaped markdown as body", name)
        html = f"<html><body><pre>{md}</pre></body></html>"

    # store article
    conn = repo.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (person_id, title, markdown, html) VALUES (?, ?, ?, ?)",
        (person_id, f"Article: {name}", md, html),
    )
    conn.commit()
    conn.close()

    # write to site
    Path("site").mkdir(exist_ok=True)
    out_html = Path("site") / (slugify(name) + ".html")
    out_html.write_text(html, encoding="utf-8")
    print("Wrote:", out_html)

    # 5) Snapshot diff: compute a simple diff against last snapshot
    try:
        conn = repo.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT diff FROM snapshots WHERE person_id = ? ORDER BY snapshot_date DESC LIMIT 1", (person_id,))
        row = cur.fetchone()
        previous_concat = row["diff"] if row else ""
        current_concat = "\n".join(a.get("title", "") + "\n" + a.get("content", "") for a in activities)
        diffl = compute_diff(previous_concat or "", current_concat or "")
        if diffl:
            cur.execute("INSERT INTO snapshots (person_id, snapshot_date, diff) VALUES (?, date('now'), ?)", (person_id, "\n".join(diffl)))
            conn.commit()
        conn.close()
    except Exception as e:
        print("Snapshot step failed:", e)


def main():
    print("Bootstrapping DB and directories...")
    Path("data").mkdir(exist_ok=True)
    Path("site").mkdir(exist_ok=True)
    repo.init_db(schema_path="src/db/schema.sql")

    persons = read_persons()
    skip_network = bool(os.getenv("SKIP_NETWORK"))
    for p in persons:
        process_person(p, skip_network=skip_network)

    print("Done")


import csv
from jinja2 import Template

def generate_index():
    with open("data/persons.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        persons = list(reader)

    template = Template("""
    <html><body>
    <h1>人物一覧</h1>
    <ul>
    {% for p in persons %}
      <li><a href="{{p['person_id']}}.html">{{p['name']}}</a></li>
    {% endfor %}
    </ul>
    </body></html>
    """)
    html = template.render(persons=persons)

    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    import sys
    # allow generating only the index without running the full main flow
    if "--index-only" in sys.argv:
        generate_index()
    else:
        main()
        generate_index()
