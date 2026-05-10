"""
ATHOS Memory Extractor — extrait automatiquement les faits importants
des conversations et les persiste en §-format dans le Drive.
Appelé de manière asynchrone après chaque échange significatif.
"""
import json, urllib.request, threading
from pathlib import Path
from datetime import datetime

DRIVE   = Path.home() / "Library/CloudStorage/GoogleDrive-contact@ex-nihilo.agency/Mon Drive/CLAUDE AI/memory"
ENV     = Path(__file__).parent.parent / ".env"

# Seuil : extraire seulement si échange > N chars (évite le bruit)
MIN_LENGTH = 80

def _load_key() -> str:
    if not ENV.exists(): return ""
    for line in ENV.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""

def _extract_facts(user_msg: str, reply: str, api_key: str) -> list[str]:
    """Demande à Claude d'extraire les faits mémorisables en §-format."""
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",   # rapide + pas cher
        "max_tokens": 200,
        "system": (
            "Tu analyses un échange avec ATHOS et extrais UNIQUEMENT les faits "
            "mémorisables à long terme (projets, décisions, préférences, "
            "infos réseau/devices, règles, contexte important). "
            "Format strict §-compressé, une ligne par fait. "
            "Si rien de mémorisable : réponds juste 'RIEN'. "
            "Exemples valides:\n"
            "§proj:athos|update:agent_ReAct_opérationnel|date:2026-05-10\n"
            "§device:tv|ip:192.168.1.42|type:Apple_TV|room:salon\n"
            "§rule:clément_préfère:réponses_courtes|w:8\n"
            "§behavior:pattern:toujours_checker_réseau_avant_installation"
        ),
        "messages": [{
            "role": "user",
            "content": f"User: {user_msg[:300]}\nATHOS: {reply[:400]}\n\nFaits à mémoriser ?"
        }]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            text = json.loads(r.read())["content"][0]["text"].strip()
        if text == "RIEN" or not text.startswith("§"):
            return []
        return [l.strip() for l in text.splitlines() if l.strip().startswith("§")]
    except:
        return []

def _route_and_save(facts: list[str]):
    """Route chaque §-ligne dans le bon fichier mémoire."""
    routing = {
        "§proj":     "athos_projects.mem",
        "§device":   "athos_behaviors.mem",    # devices = behaviors contextuels
        "§rule":     "athos_feedback.mem",
        "§behavior": "athos_behaviors.mem",
        "§learned":  "athos_behaviors.mem",
        "§network":  "athos_behaviors.mem",
        "§client":   "athos_projects.mem",
        "§conv":     "athos_conv.mem",
    }
    saved = {}
    for fact in facts:
        target = "athos_behaviors.mem"   # fallback
        for prefix, fname in routing.items():
            if fact.startswith(prefix):
                target = fname
                break
        file_path = DRIVE / target
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"\n{fact}\n")
            saved[target] = saved.get(target, 0) + 1
        except:
            pass
    return saved

def extract_and_save_async(user_msg: str, reply: str):
    """Lance l'extraction en thread background — non bloquant."""
    if len(user_msg) + len(reply) < MIN_LENGTH:
        return

    api_key = _load_key()
    if not api_key or api_key.startswith("sk-ant-..."):
        return

    def _run():
        facts = _extract_facts(user_msg, reply, api_key)
        if facts:
            saved = _route_and_save(facts)
            ts = datetime.now().strftime("%H:%M")
            print(f"  [ATHOS memory] {ts} — {len(facts)} faits extraits → {list(saved.keys())}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
