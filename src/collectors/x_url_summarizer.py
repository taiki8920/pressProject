"""Summarize a given X/Twitter URL's page using OpenAI's Chat API.

This module does NOT use the Twitter API. It downloads the page HTML, extracts
text using BeautifulSoup, and then calls OpenAI to produce a short factual
summary. It includes retries, logging, and a fallback that returns an
abbreviated cleaned text when the LLM call fails.

Environment variables:
- OPENAI_API_KEY: required for OpenAI calls
"""
from typing import Optional
import os
import time
import logging

import requests
from bs4 import BeautifulSoup

try:
    import openai
except Exception:
    openai = None  # type: ignore

LOGGER = logging.getLogger(__name__)
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"


DEFAULT_PROMPT = (
    "You are a concise, factual summarizer. Given the text of a social media "
    "post's linked page, produce a short (<=200 words) factual summary focusing "
    "on statements, events, and times. Do not hallucinate. If the page contains "
    "quotes or named persons, include them. Prepend the summary with a one-line "
    "bullet containing the source URL."
)


def _fetch_page_text(url: str, timeout: int = 10) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "press-project-bot/1.0"})
        if resp.status_code != 200:
            LOGGER.warning("Failed to fetch %s: status=%s", url, resp.status_code)
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        # remove scripts and styles
        for s in soup(["script", "style", "noscript"]):
            s.extract()
        text = soup.get_text(separator="\n")
        # collapse whitespace and trim
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        joined = "\n\n".join(lines)
        return joined[:30000]
    except Exception as e:
        LOGGER.exception("Error fetching page %s: %s", url, e)
        return None


def _call_openai_chat(system: str, user: str, model: str = "gpt-3.5-turbo", max_tokens: int = 512) -> Optional[str]:
    if openai is None:
        LOGGER.warning("openai package not installed; skipping LLM call")
        return None
    api_key = os.getenv(OPENAI_API_KEY_ENV)
    if not api_key:
        LOGGER.warning("OPENAI_API_KEY not set; skipping LLM call")
        return None
    openai.api_key = api_key
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        choices = resp.get("choices") or []
        if not choices:
            return None
        return choices[0]["message"]["content"].strip()
    except Exception:
        LOGGER.exception("OpenAI API call failed")
        return None


def summarize_url_with_gpt(url: str, prompt_template: Optional[str] = None, retries: int = 3) -> Optional[str]:
    """Summarize the page at `url` using OpenAI with retries and fallback.

    Returns a short summary string, or None if nothing could be produced.
    """
    prompt = prompt_template or DEFAULT_PROMPT
    page_text = _fetch_page_text(url)
    if not page_text:
        LOGGER.info("No page text available for %s", url)
        return None

    # Prepare user content (truncate to keep within token limits)
    user_content = f"URL: {url}\n\nContent:\n{page_text[:20000]}"

    attempt = 0
    summary = None
    while attempt < retries:
        attempt += 1
        LOGGER.info("LLM attempt %d for %s", attempt, url)
        summary = _call_openai_chat(prompt, user_content)
        if summary:
            summary = f"Source: {url}\n\n{summary}"
            break
        backoff = 2 ** attempt
        LOGGER.warning("LLM attempt %d failed, backing off %ds", attempt, backoff)
        time.sleep(backoff)

    if not summary:
        # Fallback: return a short excerpt of the cleaned page text
        LOGGER.warning("All LLM attempts failed for %s; returning fallback excerpt", url)
        excerpt = "\n\n".join(page_text.splitlines()[:10])
        summary = f"Source: {url}\n\n(FALLBACK) {excerpt[:2000]}"

    # Persist LLM log to DB if possible, but do not raise on failure
    try:
        from src.db import repository as repo

        try:
            repo.insert_llm_log(None, "x_summary", url, prompt, summary)
        except Exception:
            LOGGER.exception("Failed to insert llm_log for %s", url)
    except Exception:
        LOGGER.debug("repository not available to log llm response")

    return summary

