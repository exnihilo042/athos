"""ATHOS Web — recherche web, sources académiques, fetch de pages"""
import json, urllib.request, urllib.parse
from pathlib import Path

# ── DuckDuckGo ────────────────────────────────────────────────────────────────

def search_web(query: str, max_results: int = 6) -> list[dict]:
    """Retourne [{"title", "url", "snippet"}] depuis DuckDuckGo."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddg:
            results = list(ddg.text(query, max_results=max_results))
        return [{"title": r.get("title",""), "url": r.get("href",""),
                 "snippet": r.get("body","")} for r in results]
    except Exception as e:
        return [{"title": "Erreur", "url": "", "snippet": str(e)}]

def search_news(query: str, max_results: int = 5) -> list[dict]:
    """Actualités récentes via DuckDuckGo News."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddg:
            results = list(ddg.news(query, max_results=max_results))
        return [{"title": r.get("title",""), "url": r.get("url",""),
                 "snippet": r.get("body",""), "date": r.get("date","")} for r in results]
    except Exception as e:
        return [{"title": "Erreur", "url": "", "snippet": str(e), "date": ""}]

# ── Fetch page ────────────────────────────────────────────────────────────────

def fetch_page(url: str, max_chars: int = 4000) -> str:
    """Récupère et nettoie le texte d'une page web."""
    try:
        from bs4 import BeautifulSoup
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read()
        soup = BeautifulSoup(html, "lxml")
        # Supprimer nav, scripts, styles
        for tag in soup(["script","style","nav","footer","header","aside","form"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:max_chars]
    except Exception as e:
        return f"Erreur fetch : {e}"

# ── arXiv ─────────────────────────────────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 4) -> list[dict]:
    """Cherche des articles académiques sur arXiv."""
    try:
        import arxiv
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results,
                              sort_by=arxiv.SortCriterion.Relevance)
        results = []
        for r in client.results(search):
            results.append({
                "title":    r.title,
                "authors":  ", ".join(a.name for a in r.authors[:3]),
                "abstract": r.summary[:400],
                "url":      r.pdf_url,
                "date":     r.published.strftime("%Y-%m") if r.published else ""
            })
        return results
    except Exception as e:
        return [{"title": "Erreur arXiv", "abstract": str(e), "url": "", "authors": "", "date": ""}]

def search_wikipedia(query: str) -> dict:
    """Résumé Wikipedia via l'API REST (sans clé)."""
    try:
        encoded = urllib.parse.quote(query.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "ATHOS/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        # Essai en français
        if data.get("type") == "disambiguation":
            url_fr = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            with urllib.request.urlopen(
                urllib.request.Request(url_fr, headers={"User-Agent": "ATHOS/1.0"}), timeout=8
            ) as r:
                data = json.loads(r.read())
        return {"title": data.get("title",""), "summary": data.get("extract","")[:800],
                "url": data.get("content_urls",{}).get("desktop",{}).get("page","")}
    except Exception as e:
        return {"title": "", "summary": f"Erreur Wikipedia : {e}", "url": ""}

# ── Formateur ─────────────────────────────────────────────────────────────────

def format_search_results(results: list[dict], source: str = "web") -> str:
    """Formate les résultats pour injection dans le contexte LLM."""
    if not results:
        return "Aucun résultat trouvé."
    lines = [f"[SOURCE:{source.upper()}]"]
    for i, r in enumerate(results, 1):
        if source == "arxiv":
            lines.append(f"{i}. {r['title']} ({r['date']}) — {r['authors']}\n   {r['abstract']}")
        else:
            lines.append(f"{i}. {r['title']}\n   {r.get('snippet','')[:200]}")
    return "\n".join(lines)
