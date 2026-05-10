"""
ATHOS Quality Pipeline
Génération → Autocritique (Haiku) → Web si besoin → Raffinement (Sonnet)
Coût typique : +0.001€ par échange (haiku ~50 tokens)
"""
import json, urllib.request, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

def _key() -> str:
    return config.ANTHROPIC_KEY

def _claude(system: str, msg: str, model: str, max_tokens: int, key: str) -> str:
    payload = json.dumps({
        "model": model, "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": msg}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())["content"][0]["text"].strip()

# ── Autocritique ──────────────────────────────────────────────────────────────

def critique(question: str, draft: str, api_key: str = "") -> dict:
    """
    Évalue la réponse draft avec claude-haiku (rapide, cheap).
    Retourne {"score": 1-10, "issues": [...], "web_queries": [...], "needs_web": bool}
    """
    key = api_key or _key()
    if not key: return {"score": 10, "issues": [], "web_queries": [], "needs_web": False}

    # Ne pas critiquer les réponses triviales
    if len(draft) < 60 or any(w in question.lower() for w in
                               ["lance", "go", "oui", "annule", "ok", "merci"]):
        return {"score": 10, "issues": [], "web_queries": [], "needs_web": False}

    system = (
        "Tu es l'autocritique d'ATHOS. Évalue cette réponse IA à la question posée. "
        "Réponds UNIQUEMENT en JSON valide : "
        '{"score":N,"issues":["..."],"web_queries":["..."],"needs_web":true/false} '
        "score=1-10. needs_web=true si la réponse nécessite des données récentes/factuelles. "
        "web_queries = 1-2 requêtes web qui amélioreraient la réponse (vide si score>=8)."
    )
    msg = f"Question: {question[:200]}\nRéponse: {draft[:400]}"
    try:
        raw = _claude(system, msg, "claude-haiku-4-5-20251001", 150, key)
        # Parser JSON robuste
        start = raw.find("{"); end = raw.rfind("}") + 1
        data  = json.loads(raw[start:end]) if start >= 0 else {}
        return {
            "score":       int(data.get("score", 7)),
            "issues":      data.get("issues", []),
            "web_queries": data.get("web_queries", []),
            "needs_web":   bool(data.get("needs_web", False))
        }
    except Exception:
        return {"score": 7, "issues": [], "web_queries": [], "needs_web": False}

# ── Raffinement ───────────────────────────────────────────────────────────────

def refine(question: str, draft: str, web_context: str,
           system_prompt: str, api_key: str = "") -> str:
    """
    Raffine la réponse en incorporant le contexte web.
    N'est appelé que si critique.needs_web == True.
    """
    key = api_key or _key()
    if not key: return draft

    system = system_prompt + "\n\nRÈGLE : Tu reçois une ébauche de réponse + des sources web. " \
             "Améliore la réponse en intégrant les faits pertinents. " \
             "Reste concis (1-3 phrases pour la voix). Ne cite pas les sources explicitement."
    msg = (f"Question originale : {question}\n\n"
           f"Ébauche : {draft}\n\n"
           f"Sources web :\n{web_context}\n\n"
           f"Réponse améliorée :")
    try:
        return _claude(system, msg, "claude-sonnet-4-6", 300, key)
    except Exception:
        return draft

# ── Pipeline complet ──────────────────────────────────────────────────────────

def quality_pipeline(question: str, draft: str, system_prompt: str,
                     api_key: str = "", on_status=None) -> str:
    """
    Pipeline complet : draft → critique → (web) → raffinement.
    on_status(msg) : callback pour streamer le statut vers la PWA.
    Retourne la réponse finale.
    """
    from web import search_web, format_search_results

    # 1. Autocritique
    c = critique(question, draft, api_key)

    if c["score"] >= 8 or not c["needs_web"]:
        return draft   # réponse déjà bonne

    # 2. Recherche web
    if on_status: on_status(f"Vérification : {c['web_queries'][0] if c['web_queries'] else '...'}")
    all_results = []
    for q in c["web_queries"][:2]:
        all_results += search_web(q, max_results=4)

    if not all_results:
        return draft

    web_ctx = format_search_results(all_results[:6], "web")

    # 3. Raffinement
    if on_status: on_status("Raffinement...")
    refined = refine(question, draft, web_ctx, system_prompt, api_key)
    return refined
