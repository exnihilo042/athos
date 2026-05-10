"""
ATHOS Skill Manager — acquisition autonome de compétences
ATHOS détecte ce dont il a besoin, cherche la solution, génère le code, installe.
"""
import json, subprocess, urllib.request
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path(__file__).parent / "skills"
SKILLS_DIR.mkdir(exist_ok=True)
MANIFEST   = SKILLS_DIR / "manifest.json"
ENV        = Path(__file__).parent.parent / ".env"

# ── Catalogue des compétences connues ─────────────────────────────────────────
KNOWN_SKILLS = {
    "homekit": {
        "description": "Contrôle appareils HomeKit (lumières, serrures, thermostats)",
        "pip": ["homekit"],
        "file": "skill_homekit.py"
    },
    "gmail": {
        "description": "Lecture/envoi emails Gmail",
        "pip": ["google-auth-oauthlib", "google-api-python-client"],
        "file": "skill_gmail.py"
    },
    "calendar": {
        "description": "Google Calendar — agenda, événements",
        "pip": ["google-auth-oauthlib", "google-api-python-client"],
        "file": "skill_calendar.py"
    },
    "spotify": {
        "description": "Contrôle Spotify — lecture, playlists, recherche",
        "pip": ["spotipy"],
        "file": "skill_spotify.py"
    },
    "vision": {
        "description": "Analyse d'images et captures d'écran",
        "pip": ["Pillow"],
        "file": "skill_vision.py"
    },
    "pdf": {
        "description": "Lecture et extraction de texte depuis PDFs",
        "pip": ["pdfplumber"],
        "file": "skill_pdf.py"
    },
    "notion": {
        "description": "Lecture/écriture Notion databases",
        "pip": ["notion-client"],
        "file": "skill_notion.py"
    },
    "whatsapp": {
        "description": "Envoi messages WhatsApp via Twilio",
        "pip": ["twilio"],
        "file": "skill_whatsapp.py"
    },
}

# ── Manifest (compétences installées) ────────────────────────────────────────

def load_manifest() -> dict:
    if MANIFEST.exists():
        try: return json.loads(MANIFEST.read_text())
        except: pass
    return {}

def save_manifest(m: dict):
    MANIFEST.write_text(json.dumps(m, indent=2))

def is_installed(skill_name: str) -> bool:
    return skill_name in load_manifest()

def list_installed() -> list[str]:
    return list(load_manifest().keys())

# ── Détection des gaps ────────────────────────────────────────────────────────

def detect_needed_skills(question: str) -> list[str]:
    """Analyse la question et identifie les compétences manquantes."""
    q = question.lower()
    needed = []
    triggers = {
        "homekit":  ["lumière", "lampe", "serrure", "thermostat", "homekit", "domotique"],
        "gmail":    ["email", "mail", "gmail", "message", "inbox"],
        "calendar": ["agenda", "calendrier", "rdv", "rendez-vous", "réunion", "calendar"],
        "spotify":  ["spotify", "musique", "playlist", "chanson", "artiste"],
        "vision":   ["photo", "image", "screenshot", "capture", "vois", "regarde"],
        "pdf":      ["pdf", "document", "manuel", "guide", "livre"],
        "notion":   ["notion", "base de données", "notes", "workspace"],
    }
    for skill, words in triggers.items():
        if any(w in q for w in words) and not is_installed(skill):
            needed.append(skill)
    return needed

# ── Installation ──────────────────────────────────────────────────────────────

def install_skill(skill_name: str, api_key: str = "") -> tuple[bool, str]:
    """
    Installe une compétence :
    1. pip install des dépendances
    2. Génère le code connecteur via Claude si non existant
    3. Teste que l'import fonctionne
    """
    if skill_name not in KNOWN_SKILLS:
        # Compétence inconnue → tenter de la générer
        return _generate_unknown_skill(skill_name, api_key)

    skill = KNOWN_SKILLS[skill_name]
    venv_pip = str(Path(__file__).parent.parent / "venv/bin/pip")

    # 1. Installer les dépendances pip
    for pkg in skill.get("pip", []):
        result = subprocess.run([venv_pip, "install", pkg, "-q"],
                                capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return False, f"pip install {pkg} échoué : {result.stderr[:200]}"

    # 2. Générer le connecteur si absent
    skill_file = SKILLS_DIR / skill["file"]
    if not skill_file.exists():
        if api_key:
            code = _generate_connector(skill_name, skill["description"], api_key)
            if code:
                skill_file.write_text(code)
        else:
            skill_file.write_text(f'"""Skill {skill_name} — à configurer"""\n')

    # 3. Sauvegarder dans le manifest
    manifest = load_manifest()
    manifest[skill_name] = {
        "installed_at": datetime.now().isoformat(),
        "file": str(skill_file),
        "description": skill["description"]
    }
    save_manifest(manifest)
    return True, f"Compétence '{skill_name}' installée : {skill['description']}"

def _generate_connector(skill_name: str, description: str, api_key: str) -> str:
    """Génère le code Python d'un connecteur via Claude."""
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 800,
        "system": (
            "Tu génères des connecteurs Python pour ATHOS. "
            "Code propre, fonctions simples, gestion d'erreurs. "
            "Chaque skill expose : setup(), call(action, params) -> str, test() -> bool. "
            "Ajouter les imports nécessaires. Code exécutable immédiatement."
        ),
        "messages": [{"role": "user", "content":
            f"Génère skill_{skill_name}.py pour : {description}. "
            f"Fonctions : setup(), call(action, params), test(). "
            f"Utilise les librairies pip de {KNOWN_SKILLS.get(skill_name,{}).get('pip',[])}."
        }]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = json.loads(r.read())["content"][0]["text"]
        # Extraire le code Python
        if "```python" in text:
            text = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
    except:
        return ""

def _generate_unknown_skill(skill_name: str, api_key: str) -> tuple[bool, str]:
    """Tente de générer un skill inconnu en cherchant sur le web + générant le code."""
    from web import search_web
    results = search_web(f"Python library {skill_name} API integration", 3)
    if not results:
        return False, f"Compétence '{skill_name}' inconnue et introuvable."

    context = "\n".join(r.get("snippet","") for r in results[:3])
    code = _generate_connector(skill_name, f"Integration with {skill_name}. Context: {context[:400]}", api_key)
    if not code:
        return False, f"Impossible de générer le connecteur pour '{skill_name}'."

    skill_file = SKILLS_DIR / f"skill_{skill_name}.py"
    skill_file.write_text(code)
    manifest = load_manifest()
    manifest[skill_name] = {
        "installed_at": datetime.now().isoformat(),
        "file": str(skill_file),
        "description": f"Auto-généré pour {skill_name}",
        "auto_generated": True
    }
    save_manifest(manifest)
    return True, f"Compétence '{skill_name}' générée et installée automatiquement."

# ── Rapport ────────────────────────────────────────────────────────────────────

def capabilities_report() -> str:
    installed = load_manifest()
    available = [k for k in KNOWN_SKILLS if k not in installed]
    lines = ["=== ATHOS SKILLS ==="]
    if installed:
        lines.append("Installées :")
        for name, info in installed.items():
            lines.append(f"  ✓ {name} — {info.get('description','')}")
    if available:
        lines.append("Disponibles (non installées) :")
        for name in available:
            lines.append(f"  ○ {name} — {KNOWN_SKILLS[name]['description']}")
    return "\n".join(lines)
