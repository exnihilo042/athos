"""ATHOS Voice Server — Agent ReAct + confirmation + mémoire Drive"""
import os, sys, json, urllib.request, urllib.error, subprocess, threading, uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
import config
import engine_router
import session_kernel
from auth import request_authorized
from memory_extractor import extract_and_save_async

ANTHROPIC_KEY = config.ANTHROPIC_KEY
OPENAI_KEY = config.OPENAI_KEY
OPENAI_ENABLED = config.OPENAI_ENABLED
GROK_KEY = config.GROK_KEY
OPENAI_MODEL = config.OPENAI_MODEL
GROK_MODEL = config.GROK_MODEL
ACCESS_TOKEN = config.ATHOS_ACCESS_TOKEN
DRIVE = config.DRIVE
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

# ── Threading HTTP server ─────────────────────────────────────────────────────
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── Permission prompts (ToolBus → UI → réponse) ───────────────────────────────
_permits: dict[str, dict] = {}
_permits_lock = threading.Lock()

def make_permission_checker(sse_fn):
    """Crée un permission_check bloquant pour cette requête SSE."""
    def check(tool_name: str, inputs: dict) -> bool:
        perm_id = uuid.uuid4().hex
        evt = threading.Event()
        with _permits_lock:
            _permits[perm_id] = {"event": evt, "approved": False}
        safe_inputs = {k: str(v)[:200] for k, v in inputs.items()}
        sse_fn({"permission_required": True, "id": perm_id,
                "tool": tool_name, "inputs": safe_inputs})
        evt.wait(timeout=60)   # 60s pour répondre
        with _permits_lock:
            result = _permits.pop(perm_id, {})
        return result.get("approved", False)
    return check

# ── Engine ────────────────────────────────────────────────────────────────────
_engine = {"current": "none", "degraded": False}

def _detect():
    return engine_router.first_available(_available_engines())

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

def is_authorized(headers) -> bool:
    return request_authorized(headers, ACCESS_TOKEN)

def _available_engines() -> list[str]:
    return engine_router.available_engines(
        anthropic_key=ANTHROPIC_KEY,
        openai_key=OPENAI_KEY,
        openai_enabled=OPENAI_ENABLED,
        grok_key=GROK_KEY,
        has_ollama=lambda: bool(_ollama_models()),
        has_chatgpt_plus=engine_router.chatgpt_plus_available,
        has_claude_code=engine_router.claude_code_available,
    )

_engine["current"] = _detect()

def degrade_engine(reason: str):
    available = _available_engines()
    if not available:
        _engine["current"] = "none"
        _engine["degraded"] = True
        return "none"
    next_engine = engine_router.next_engine(_engine["current"], available)
    if next_engine == _engine["current"]:
        return next_engine
    _engine["current"] = next_engine
    _engine["degraded"] = True
    msg = f"Je suis passé sur {next_engine.upper()}, Clément. Je continue avec le moteur disponible."
    _notify("A.T.H.O.S.", f"Basculé {next_engine.upper()} : {reason}", "Basso")
    _write_alert("engine_alert.json", {"alert": True, "engine": next_engine, "msg": msg})
    return next_engine

def degrade_to_ollama(reason: str):
    if _engine["current"] == "ollama": return
    _engine["current"] = "ollama"
    _engine["degraded"] = True
    msg = "Je suis passé sur Ollama, Clément. Moins performant. Je te préviendrai quand Claude reviendra."
    _notify("A.T.H.O.S.", f"Basculé Ollama : {reason}", "Basso")
    _write_alert("engine_alert.json", {"alert": True, "engine": "ollama", "msg": msg})

# ── Historique session ────────────────────────────────────────────────────────
_history: list[dict] = []

def load_last_conversation():
    """Charge la dernière conversation depuis athos_conv.mem dans _history"""
    kernel_messages = session_kernel.latest_messages(limit=12)
    if kernel_messages:
        _history.extend(kernel_messages)
        return

    f = DRIVE / "athos_conv.mem"
    if not f.exists(): return
    lines = f.read_text("utf-8").splitlines()
    conv_lines = [l for l in lines if l.startswith("§conv:")][-12:]  # last 6 exchanges
    for line in conv_lines:
        parts = line.split("|")
        if len(parts) >= 3:
            ts = parts[0].split(":", 1)[1]
            u = parts[1].split(":", 1)[1] if len(parts) > 1 else ""
            a = parts[2].split(":", 1)[1] if len(parts) > 2 else ""
            if u: _history.append({"role": "user", "content": u})
            if a: _history.append({"role": "assistant", "content": a})
    while len(_history) > 12:
        _history.pop(0)

load_last_conversation()  # Charge la dernière conv au démarrage

def push(role: str, content: str):
    _history.append({"role": role, "content": content})
    while len(_history) > 12:   # 6 échanges max
        _history.pop(0)

def get_history() -> list:
    return list(_history)

# ── Mémoire contextuelle ──────────────────────────────────────────────────────
def load_context() -> str:
    parts = []
    kernel_ctx = session_kernel.context_pack(max_chars=1200)
    if kernel_ctx:
        parts.append(kernel_ctx)
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
    return "\n".join(parts)[:1800]

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

# ── Grok streaming ────────────────────────────────────────────────────────────
CHATGPT_LIMIT_MARKERS = ["usage limit", "upgrade to pro", "purchase more credits"]

def chatgpt_plus_stream(msg: str, send, on_terminal=None):
    ctx = load_context()
    prompt = f"Tu es Athos. Réponds en français, directement.\n\nCONTEXTE:\n{ctx}\n\nUSER:\n{msg}"
    codex_bin = engine_router.chatgpt_plus_path()
    if not codex_bin:
        raise RuntimeError("ChatGPT Plus CLI introuvable")
    result = subprocess.run(
        [codex_bin, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt],
        capture_output=True, text=True, timeout=180,
        cwd=str(config.ATHOS_PATH)
    )
    # Stderr → terminal panel
    if result.stderr.strip() and on_terminal:
        for line in result.stderr.strip().splitlines():
            on_terminal(line)
    output = result.stdout.strip()
    if result.returncode != 0 or any(m in (result.stdout + result.stderr).lower() for m in CHATGPT_LIMIT_MARKERS):
        raise RuntimeError(f"ChatGPT Plus limite atteinte : {(result.stdout + result.stderr)[:120]}")
    send(output)
    return output


def claude_code_stream(msg: str, send, on_terminal=None):
    """on_terminal(line) → streame les logs internes vers le terminal panel."""
    ctx = load_context()
    prompt = f"Tu es Athos. Réponds en français, directement.\n\nCONTEXTE:\n{ctx}\n\nUSER:\n{msg}"
    proc = subprocess.Popen(
        ["claude", "-p", prompt, "--output-format", "text"],
        cwd=str(config.ATHOS_PATH),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )
    stdout_lines = []
    # Lire stderr en thread → terminal panel
    def drain_stderr():
        for line in proc.stderr:
            line = line.rstrip()
            if line and on_terminal:
                on_terminal(line)
    import threading
    t = threading.Thread(target=drain_stderr, daemon=True)
    t.start()
    for line in proc.stdout:
        stdout_lines.append(line)
    proc.wait(timeout=180)
    t.join(timeout=5)
    full = "".join(stdout_lines).strip()
    if not full or proc.returncode != 0:
        raise RuntimeError(f"Claude Code échec (code {proc.returncode})")
    send(full)
    return full


# ── Grok streaming ────────────────────────────────────────────────────────────
def grok_stream(msg: str, send):
    ctx      = load_context()
    from agent import SYSTEM
    messages = [{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
    messages += get_history()
    messages += [{"role": "user", "content": msg}]
    api_key = GROK_KEY
    if not api_key:
        send("Erreur: GROK_API_KEY manquante")
        return ""
    payload  = json.dumps({
        "model": GROK_MODEL, "stream": True, "messages": messages
    }).encode()
    req = urllib.request.Request("https://api.x.ai/v1/chat/completions", data=payload,
                                  headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"})
    full = ""
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for line in r:
                if not line.strip(): continue
                if line.startswith(b"data: "):
                    line = line[6:]
                try:
                    chunk = json.loads(line)
                    t = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if t:
                        full += t
                        send(t)
                except: continue
    except Exception as e:
        send(f"Erreur Grok: {str(e)}")
    return full

# ── ChatGPT streaming ─────────────────────────────────────────────────────────
def chatgpt_stream(msg: str, send):
    ctx      = load_context()
    from agent import SYSTEM
    messages = [{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
    messages += get_history()
    messages += [{"role": "user", "content": msg}]
    api_key = OPENAI_KEY
    if not api_key:
        send("Erreur: OPENAI_API_KEY manquante")
        return ""
    payload  = json.dumps({
        "model": OPENAI_MODEL, "stream": True, "messages": messages
    }).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=payload,
                                  headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"})
    full = ""
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for line in r:
                if not line.strip(): continue
                if line.startswith(b"data: "):
                    line = line[6:]
                try:
                    chunk = json.loads(line)
                    t = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if t:
                        full += t
                        send(t)
                except: continue
    except Exception as e:
        send(f"Erreur ChatGPT: {str(e)}")
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
        if self.path.split("?")[0] == "/api/session":
            if not self._require_auth():
                return
            self._json(session_kernel.status()); return

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

    def _require_auth(self) -> bool:
        if is_authorized(self.headers):
            return True
        self._json({"error": "unauthorized", "auth_required": True}, 401)
        return False

    def do_POST(self):
        p = self.path
        if p.startswith("/api/") and not self._require_auth():
            return

        if p == "/api/status":
            b = load_budget()
            model = {
                "chatgpt_plus": "ChatGPT Plus via ChatGPT Plus CLI",
                "claude_code": "Claude Code Pro",
                "anthropic_api": "claude-sonnet-4-6",
                "claude": "claude-sonnet-4-6",
                "grok": GROK_MODEL,
                "chatgpt": OPENAI_MODEL,
                "ollama": _best_model(),
                "none": "none"
            }.get(_engine["current"], "unknown")
            kernel = session_kernel.status()
            self._json({"engine": _engine["current"], "degraded": _engine["degraded"],
                        "model": model,
                        "engine_order": engine_router.configured_order(),
                        "available_engines": _available_engines(),
                        "openai_enabled": OPENAI_ENABLED,
                        "session_events": kernel["events"],
                        "session_file": kernel["file"],
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
                attempted = set()
                reply = ""

                while _engine["current"] not in attempted:
                    engine = _engine["current"]
                    attempted.add(engine)

                    if engine == "chatgpt_plus":
                        sse({"action": "chatgpt_plus", "label": "ChatGPT Plus — CLI", "result": ""})
                        try:
                            reply = chatgpt_plus_stream(
                                msg,
                                lambda t: sse({"t": t}),
                                on_terminal=lambda line: sse({"toolbus": "stderr", "data": {"chunk": line, "pid": 0}}),
                            )
                            push("user", msg); push("assistant", reply)
                            save_exchange(msg, reply)
                            log_exchange(msg, reply, "chatgpt_plus")
                            session_kernel.record_exchange(msg, reply, "chatgpt_plus")
                            break
                        except RuntimeError as e:
                            next_eng = degrade_engine(str(e)[:80])
                            session_kernel.record_action("failover", f"chatgpt_plus → {next_eng}", str(e)[:200], engine="chatgpt_plus")
                            sse({"action": "failover", "label": f"chatgpt_plus → {next_eng}", "result": str(e)[:80]})
                            if next_eng == "none":
                                sse({"t": "Aucun moteur disponible."}); break
                            continue

                    elif engine == "claude_code":
                        sse({"action": "claude_code", "label": "Claude Code Pro — subscription", "result": ""})
                        try:
                            reply = claude_code_stream(
                                msg,
                                lambda t: sse({"t": t}),
                                on_terminal=lambda line: sse({"toolbus": "stderr", "data": {"chunk": line, "pid": 0}}),
                            )
                            push("user", msg); push("assistant", reply)
                            save_exchange(msg, reply)
                            log_exchange(msg, reply, "claude_code")
                            session_kernel.record_exchange(msg, reply, "claude_code")
                            break
                        except RuntimeError as e:
                            next_eng = degrade_engine(str(e)[:80])
                            sse({"action": "failover", "label": f"claude_code → {next_eng}", "result": str(e)[:80]})
                            if next_eng == "none":
                                sse({"t": "Aucun moteur disponible."}); break
                            continue

                    elif engine in ("anthropic_api", "claude"):
                        try:
                            from agent import run_agent, SYSTEM
                            ctx     = load_context()
                            system  = SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")

                            def on_action(name, inputs, result):
                                label = (inputs.get("command") or inputs.get("script","")
                                         or inputs.get("query","") or name)[:60]
                                session_kernel.record_action(name, label, result[:200], engine=engine)
                                sse({"action": name, "label": label, "result": result[:200]})

                            def on_stream(event_type, data):
                                """ToolBus — stdout/stderr/start/done en temps réel vers UI."""
                                sse({"toolbus": event_type, **data})

                            permission_check = make_permission_checker(sse)

                            draft = run_agent(msg, system, get_history(), ANTHROPIC_KEY,
                                             on_action, on_stream, permission_check)

                            reply = draft
                            if not draft.startswith("▶") and len(draft) > 80:
                                from quality import quality_pipeline
                                def on_qstatus(s):
                                    sse({"action": "quality", "label": s, "result": ""})
                                reply = quality_pipeline(msg, draft, system, ANTHROPIC_KEY, on_qstatus)

                            sse({"t": reply})
                            push("user", msg); push("assistant", reply)
                            save_exchange(msg, reply)
                            log_exchange(msg, reply, engine)
                            session_kernel.record_exchange(msg, reply, engine)
                            extract_and_save_async(msg, reply)
                            track_usage(len(msg)//4 + 300, len(reply)//4)
                            break

                        except urllib.error.HTTPError as e:
                            if e.code in (402, 413, 429, 529):
                                previous = engine
                                next_engine = degrade_engine(f"HTTP {e.code}")
                                session_kernel.record_action(
                                    "failover",
                                    f"{previous} -> {next_engine}",
                                    f"HTTP {e.code}",
                                    engine=previous,
                                )
                                sse({"action": "failover", "label": f"{previous} → {next_engine}", "result": f"HTTP {e.code}"})
                                if next_engine == "none":
                                    sse({"t": "Aucun moteur disponible."})
                                    break
                                continue
                            sse({"t": f"Erreur API : {e.code}"}); break

                    elif engine == "grok":
                        sse({"action": "grok", "label": "Grok — sans outils", "result": ""})
                        buf = []
                        reply = grok_stream(msg, lambda t: (buf.append(t), sse({"t": t})))
                        push("user", msg); push("assistant", reply)
                        save_exchange(msg, reply)
                        log_exchange(msg, reply, "grok")
                        session_kernel.record_exchange(msg, reply, "grok")
                        break

                    elif engine == "chatgpt":
                        sse({"action": "chatgpt", "label": "ChatGPT — sans outils", "result": ""})
                        buf = []
                        reply = chatgpt_stream(msg, lambda t: (buf.append(t), sse({"t": t})))
                        push("user", msg); push("assistant", reply)
                        save_exchange(msg, reply)
                        log_exchange(msg, reply, "chatgpt")
                        session_kernel.record_exchange(msg, reply, "chatgpt")
                        break

                    elif engine == "ollama":
                        sse({"action": "ollama", "label": "Ollama — sans outils", "result": ""})
                        buf = []
                        reply = ollama_stream(msg, lambda t: (buf.append(t), sse({"t": t})))
                        push("user", msg); push("assistant", reply)
                        save_exchange(msg, reply)
                        log_exchange(msg, reply, "ollama")
                        session_kernel.record_exchange(msg, reply, "ollama")
                        break

                    else:
                        sse({"t": "Aucun moteur disponible."})
                        break

            except Exception as e:
                sse({"error": str(e), "t": f"Erreur : {e}"})

            sse("[DONE]"); return

        if p == "/api/kill":
            body = self._body()
            pid = body.get("pid")
            if pid:
                from agent import kill_process
                result = kill_process(int(pid))
                self._json({"ok": True, "msg": result}); return
            self._json({"ok": False, "msg": "pid manquant"}, 400); return

        if p == "/api/permit":
            body = self._body()
            perm_id = body.get("id", "")
            approved = bool(body.get("approved", False))
            with _permits_lock:
                entry = _permits.get(perm_id)
            if entry:
                entry["approved"] = approved
                entry["event"].set()
                self._json({"ok": True, "approved": approved}); return
            self._json({"ok": False, "msg": "permission introuvable"}, 404); return

        if p == "/api/processes":
            from agent import list_processes
            self._json({"processes": list_processes()}); return

        if p == "/api/transcribe":
            length = int(self.headers.get("Content-Length", 0))
            audio_bytes = self.rfile.read(length)
            if not audio_bytes:
                self._json({"error": "no audio"}, 400); return
            import tempfile, speech_recognition as sr
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            try:
                # Convertir webm → wav via ffmpeg (silencieux)
                wav_path = tmp_path.replace(".webm", ".wav")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path],
                    capture_output=True, timeout=30
                )
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as src:
                    audio = recognizer.record(src)
                # Whisper API si clé dispo, sinon Google free
                if config.OPENAI_KEY:
                    import openai
                    client = openai.OpenAI(api_key=config.OPENAI_KEY)
                    with open(wav_path, "rb") as f:
                        result = client.audio.transcriptions.create(model="whisper-1", file=f, language="fr")
                    text = result.text
                else:
                    text = recognizer.recognize_google(audio, language="fr-FR")
                self._json({"text": text})
            except Exception as e:
                self._json({"error": str(e)}, 500)
            finally:
                for f in [tmp_path, wav_path]:
                    try: Path(f).unlink()
                    except: pass
            return

        self.send_response(404); self.end_headers()


if __name__ == "__main__":
    port = 7474
    b    = load_budget()
    eng  = _engine["current"]
    model = {
        "chatgpt_plus": "ChatGPT Plus via ChatGPT Plus CLI",
        "claude_code": "Claude Code Pro",
        "anthropic_api": "claude-sonnet-4-6",
        "claude": "claude-sonnet-4-6",
        "grok": GROK_MODEL,
        "chatgpt": OPENAI_MODEL,
        "ollama": _best_model(),
        "none": "none"
    }.get(eng, "unknown")
    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║      A.T.H.O.S. — VOICE SERVER   ║")
    print(f"  ╚══════════════════════════════════╝\n")
    print(f"  Moteur  : {eng.upper()} / {model}")
    print(f"  Budget  : {b.get('total_eur', 0):.2f}€")
    print(f"  Port    : {port}\n")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
