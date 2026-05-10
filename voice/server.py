"""ATHOS Voice Server — Agent ReAct + confirmation + mémoire Drive"""
import os, sys, json, urllib.request, urllib.error, subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from memory_extractor import extract_and_save_async

load_dotenv(Path(__file__).parent.parent / ".env")

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
DRIVE  = Path.home() / "Library/CloudStorage/GoogleDrive-contact@ex-nihilo.agency/Mon Drive/CLAUDE AI/memory"
STATIC = Path(__file__).parent

# ── Budget ────────────────────────────────────────────────────────────────────
BUDGET_FILE = Path(__file__).parent.parent / "budget.json"
PRICE_IN    = 3.0  / 1_000_000
PRICE_OUT   = 15.0 / 1_000_000
ALERT_STEP  = 10.0

def load_budget() -> dict:
    try:    return json.loads(BUDGET_FILE.read_text()) if BUDGET_FILE.exists() else {}
    except: return {}

def save_budget(b: dict):
    BUDGET_FILE.write_text(json.dumps(b, indent=2))

def track_usage(in_tok: int, out_tok: int):
    b = {**{"total_eur": 0.0, "last_alert_at": 0.0, "requests": 0}, **load_budget()}
    b["total_eur"] += (in_tok * PRICE_IN + out_tok * PRICE_OUT) * 0.92
    b["requests"]  += 1
    if b["total_eur"] >= b["last_alert_at"] + ALERT_STEP:
        b["last_alert_at"] = (b["total_eur"] // ALERT_STEP) * ALERT_STEP
        save_budget(b)
        _notify("A.T.H.O.S.", f"{b['total_eur']:.0f}€ consommés sur Anthropic.", "Ping")
        _write_alert("budget_alert.json", {"alert": True, "total": round(b["total_eur"],2),
                     "msg": f"Attention Clément, {b['total_eur']:.0f} euros consommés sur l'API."})
    else:
        save_budget(b)

def _notify(title: str, msg: str, sound: str = "Glass"):
    subprocess.Popen(["osascript", "-e", f'display notification "{msg}" with title "{title}" sound name "{sound}"'])

def _write_alert(filename: str, data: dict):
    (STATIC / filename).write_text(json.dumps(data))

def _pop_alert(filename: str) -> dict:
    f = STATIC / filename
    if not f.exists(): return {"alert": False}
    d = json.loads(f.read_text())
    f.unlink()
    return d

# ── Engine ────────────────────────────────────────────────────────────────────
_engine = {"current": "none", "degraded": False}

def _detect():
    if ANTHROPIC_KEY and not ANTHROPIC_KEY.startswith("sk-ant-..."):
        return "claude"
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return "ollama"
    except:
        return "none"

def _ollama_models() -> list:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            return [m["name"] for m in json.loads(r.read()).get("models", [])]
    except:
        return []

def _best_model() -> str:
    priority = ["llama3.2:1b", "llama3.2", "phi3:mini", "mistral"]
    available = _ollama_models()
    for want in priority:
        for name in available:
            if name == want or name.startswith(want):
                return name
    return available[0] if available else "mistral"

_engine["current"] = _detect()

def degrade_to_ollama(reason: str):
    if _engine["current"] == "ollama": return
    _engine["current"] = "ollama"
    _engine["degraded"] = True
    msg = "Je suis passé sur Ollama, Clément. Moins performant. Je te préviendrai quand Claude reviendra."
    _notify("A.T.H.O.S.", f"Basculé Ollama : {reason}", "Basso")
    _write_alert("engine_alert.json", {"alert": True, "engine": "ollama", "msg": msg})

# ── Historique session ────────────────────────────────────────────────────────
_history: list[dict] = []

def push(role: str, content: str):
    _history.append({"role": role, "content": content})
    while len(_history) > 12:   # 6 échanges max
        _history.pop(0)

def get_history() -> list:
    return list(_history)

# ── Mémoire contextuelle ──────────────────────────────────────────────────────
def load_context() -> str:
    parts = []
    for fname, keys in [
        ("athos_identity.mem",  ["§id:", "§user:", "§agency:"]),
        ("athos_projects.mem",  ["status:active", "next:", "blocker:"]),
        ("athos_conv.mem",      ["§conv:"]),
    ]:
        f = DRIVE / fname
        if not f.exists(): continue
        lines = f.read_text("utf-8").splitlines()
        if fname == "athos_conv.mem":
            selected = [l for l in lines if l.startswith("§conv:")][-8:]
        else:
            selected = [l for l in lines if any(k in l for k in keys)][:6]
        if selected:
            parts.append("\n".join(selected))
    return "\n".join(parts)[:600]

def save_exchange(user: str, reply: str):
    ts   = datetime.now().strftime("%m-%dT%H:%M")
    line = f"§conv:{ts}|u:{user[:80].replace('|','/')}|a:{reply[:120].replace('|','/')}"
    try:
        f = DRIVE / "athos_conv.mem"
        lines = f.read_text("utf-8").splitlines() if f.exists() else []
        lines = [l for l in lines if l.startswith("§conv:")][-20:]
        lines.append(line)
        f.write_text("\n".join(lines) + "\n", "utf-8")
    except: pass

def log_exchange(user: str, reply: str, engine: str):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        ts    = datetime.now().strftime("%H:%M")
        entry = f"§voice:{ts}|eng:{engine}|u:{user[:80].replace('|','/')}|a:{reply[:150].replace('|','/')}\n"
        log_f = DRIVE / "logs" / f"{today}.mem"
        log_f.parent.mkdir(exist_ok=True)
        with open(log_f, "a", encoding="utf-8") as lf:
            lf.write(entry)
    except: pass

# ── Ollama streaming (fallback) ───────────────────────────────────────────────
def ollama_stream(msg: str, send):
    ctx      = load_context()
    from agent import SYSTEM
    messages = [{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
    messages += get_history()
    messages += [{"role": "user", "content": msg}]
    payload  = json.dumps({
        "model": _best_model(), "stream": True, "messages": messages
    }).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
                                  headers={"content-type": "application/json"})
    full = ""
    with urllib.request.urlopen(req, timeout=120) as r:
        for line in r:
            if not line.strip(): continue
            try:
                chunk = json.loads(line)
                t = chunk.get("message", {}).get("content", "")
                if t:
                    full += t
                    send(t)
                if chunk.get("done"): break
            except: continue
    return full

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        routes = {
            "/": "index.html", "/index.html": "index.html",
            "/manifest.json": "manifest.json",
            "/icon-192.png": "icon-192.png", "/icon-512.png": "icon-512.png",
        }
        name = routes.get(self.path.split("?")[0])
        f    = STATIC / name if name else None
        if not f or not f.exists():
            self.send_response(404); self.end_headers(); return
        mime = {".html": "text/html;charset=utf-8", ".json": "application/json;charset=utf-8",
                ".png": "image/png"}
        self.send_response(200)
        self.send_header("Content-Type", mime.get(f.suffix, "text/plain"))
        self.cors(); self.end_headers()
        self.wfile.write(f.read_bytes())

    def _body(self) -> dict:
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.cors(); self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        p = self.path

        if p == "/api/status":
            b = load_budget()
            self._json({"engine": _engine["current"], "degraded": _engine["degraded"],
                        "model": _best_model() if _engine["current"] == "ollama" else "claude-sonnet-4-6",
                        "budget_eur": round(b.get("total_eur", 0), 2)}); return

        if p == "/api/budget_alert":
            self._json(_pop_alert("budget_alert.json")); return

        if p == "/api/engine_alert":
            self._json(_pop_alert("engine_alert.json")); return

        if p == "/api/stream":
            msg = self._body().get("message", "")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.cors(); self.end_headers()

            def sse(obj):
                self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode())
                self.wfile.flush()

            try:
                if _engine["current"] == "claude":
                    try:
                        from agent import run_agent, SYSTEM
                        ctx     = load_context()
                        system  = SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")

                        def on_action(name, inputs, result):
                            label = (inputs.get("command") or inputs.get("script","")
                                     or inputs.get("query","") or name)[:60]
                            sse({"action": name, "label": label, "result": result[:200]})

                        draft = run_agent(msg, system, get_history(), ANTHROPIC_KEY, on_action)

                        # Quality pipeline — critique + web si nécessaire
                        # Seulement pour les réponses textuelles (pas les plans ▶)
                        reply = draft
                        if not draft.startswith("▶") and len(draft) > 80:
                            from quality import quality_pipeline
                            def on_qstatus(s):
                                sse({"action": "quality", "label": s, "result": ""})
                            reply = quality_pipeline(msg, draft, system, ANTHROPIC_KEY, on_qstatus)

                        sse({"t": reply})
                        push("user", msg); push("assistant", reply)
                        save_exchange(msg, reply)
                        log_exchange(msg, reply, "claude")
                        extract_and_save_async(msg, reply)
                        track_usage(len(msg)//4 + 300, len(reply)//4)

                    except urllib.error.HTTPError as e:
                        if e.code in (402, 529, 413):
                            degrade_to_ollama(f"HTTP {e.code}")
                            # fallthrough to ollama
                        else:
                            sse({"t": f"Erreur API : {e.code}"}); sse("[DONE]"); return

                if _engine["current"] == "ollama":
                    sse({"action": "ollama", "label": "Ollama — sans outils", "result": ""})
                    buf = []
                    reply = ollama_stream(msg, lambda t: (buf.append(t), sse({"t": t})))
                    push("user", msg); push("assistant", reply)
                    save_exchange(msg, reply)
                    log_exchange(msg, reply, "ollama")

                if _engine["current"] == "none":
                    sse({"t": "Aucun moteur disponible."})

            except Exception as e:
                sse({"t": f"Erreur : {e}"})

            sse("[DONE]"); return

        self.send_response(404); self.end_headers()


if __name__ == "__main__":
    port = 7474
    b    = load_budget()
    eng  = _engine["current"]
    model = _best_model() if eng == "ollama" else "claude-sonnet-4-6"
    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║      A.T.H.O.S. — VOICE SERVER   ║")
    print(f"  ╚══════════════════════════════════╝\n")
    print(f"  Moteur  : {eng.upper()} / {model}")
    print(f"  Budget  : {b.get('total_eur', 0):.2f}€")
    print(f"  Port    : {port}\n")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
