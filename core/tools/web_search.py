"""Web search tool — DuckDuckGo (free, no API key).

ATHOS uses this to fill knowledge gaps autonomously.
Inspired by JARVIS/HuggingGPT and SWE-agent's information retrieval.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import TypedDict


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search DuckDuckGo Instant Answer API — no key required."""
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    })
    url = f"https://api.duckduckgo.com/?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ATHOS/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        return [{"title": "search_error", "url": "", "snippet": str(e)}]

    results: list[SearchResult] = []

    # Abstract (main answer)
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", query),
            "url": data.get("AbstractURL", ""),
            "snippet": data["AbstractText"][:500],
        })

    # Related topics
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                "url": topic.get("FirstURL", ""),
                "snippet": topic["Text"][:300],
            })

    return results[:max_results]


def search_github(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search GitHub repos via GitHub search API (unauthenticated, 10 req/min)."""
    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    })
    url = f"https://api.github.com/search/repositories?{params}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "ATHOS/1.0",
            "Accept": "application/vnd.github.v3+json",
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        return [{"title": "github_error", "url": "", "snippet": str(e)}]

    return [
        {
            "title": item["full_name"],
            "url": item["html_url"],
            "snippet": f"⭐{item['stargazers_count']} | {item.get('description', '')[:200]}",
        }
        for item in data.get("items", [])
    ]


def fetch_raw(url: str, max_chars: int = 4000) -> str:
    """Fetch raw text from a URL (for reading docs, READMEs, etc.)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ATHOS/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="ignore")
        # Strip HTML tags naively
        import re
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw[:max_chars]
    except Exception as e:
        return f"fetch_error: {e}"


def summarize_search(query: str, max_results: int = 5) -> str:
    """Return search results as a text block for LLM context."""
    results = search(query, max_results)
    if not results:
        return f"Aucun résultat pour: {query}"
    lines = [f"RECHERCHE WEB: '{query}'"]
    for r in results:
        lines.append(f"  • {r['title']}")
        if r["snippet"]:
            lines.append(f"    {r['snippet'][:200]}")
        if r["url"]:
            lines.append(f"    → {r['url']}")
    return "\n".join(lines)
