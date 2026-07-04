"""Fetch and extract the main text of a news article from a URL.

We fetch the HTML ourselves with a browser-like User-Agent (many sites block
default bot agents) and let trafilatura strip boilerplate. If the page can't be
read (paywall / JS-only / blocked), the caller falls back to pasted text.
"""
from __future__ import annotations

import logging

import requests
import trafilatura

logger = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
_MAX_CHARS = 12000   # plenty for an article; keeps the Claude prompt bounded


def fetch_article(url: str) -> dict:
    """Return {ok, title, text} on success, or {ok: False, error} otherwise."""
    try:
        r = requests.get(
            url,
            headers={"User-Agent": _UA, "Accept-Language": "en,sv;q=0.8"},
            timeout=15,
        )
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"Article fetch failed for {url}: {e}")
        return {
            "ok": False,
            "error": "Kunde inte hämta sidan (blockerad, betalvägg eller nätverksfel). "
                     "Klistra in artikeltexten istället.",
        }

    html = r.text
    text = trafilatura.extract(html, include_comments=False, favor_precision=True)

    title = None
    try:
        meta = trafilatura.extract_metadata(html)
        title = getattr(meta, "title", None) if meta else None
    except Exception:
        pass

    if not text or len(text.strip()) < 200:
        return {
            "ok": False,
            "title": title,
            "error": "Hittade ingen läsbar artikeltext (troligen betalvägg eller JS-sida). "
                     "Klistra in artikeltexten istället.",
        }

    return {"ok": True, "title": title, "text": text.strip()[:_MAX_CHARS]}
