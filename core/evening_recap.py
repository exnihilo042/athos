"""ATHOS — Evening Recap 21h | lit les logs du jour, synthèse en notification Mac"""
import sys, subprocess, json, urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from memory_manager import read

DRIVE = config.DRIVE
ENV_FILE = config.ENV_PATH

def load_env():
    if not ENV_FILE.exists(): return {}
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def load_today_log() -> list:
    today    = datetime.now().strftime("%Y-%m-%d")
    log_file = DRIVE / "logs" / f"{today}.mem"
    if not log_file.exists():
        return []
    return [l for l in log_file.read_text("utf-8").splitlines() if l.startswith("§")]

def notify(title: str, msg: str):
    subprocess.run(["osascript", "-e",
        f'display notification "{msg}" with title "{title}" sound name "Glass"'])

def ask_claude_recap(log_lines: list, key: str) -> str:
    summary = "\n".join(log_lines[-30:])
    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 200,
        "system": "Tu es ATHOS, IA de Clément. En 2-3 phrases maximum, résume la journée depuis ces logs §-format. Direct, factuel, utile. Mentionne ce qui est resté en suspens.",
        "messages": [{"role": "user", "content": f"Logs du jour:\n{summary}\n\nRécap de la journée ?"}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"]
    except:
        return None

def local_recap(log_lines: list) -> str:
    voice_count = sum(1 for l in log_lines if "§voice:" in l)
    session_count = sum(1 for l in log_lines if "§session:" in l)
    proj_lines = [l for l in log_lines if "§proj:" in l]
    parts = []
    if voice_count: parts.append(f"{voice_count} échanges vocaux")
    if session_count: parts.append(f"{session_count} sessions Claude Code")
    if proj_lines: parts.append(f"{len(proj_lines)} mises à jour projets")
    return "Journée : " + (", ".join(parts) if parts else "journée calme.") + " Bonne nuit."

if __name__ == "__main__":
    env      = load_env()
    api_key  = env.get("ANTHROPIC_API_KEY", "")
    logs     = load_today_log()

    if api_key and not api_key.startswith("sk-ant-...") and logs:
        recap = ask_claude_recap(logs, api_key)
    else:
        recap = None

    if not recap:
        recap = local_recap(logs)

    notify("A.T.H.O.S. — Récap 21h", recap)
    print(f"[ATHOS evening] {recap}")
