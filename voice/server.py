"""ATHOS Voice Server — couche HTTP pure. Toute la logique est dans core/."""
import sys, json, subprocess, threading, uuid, tempfile, shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

import config
import session_kernel
import sync_manager
from auth import request_authorized
from memory_extractor import extract_and_save_async
from athos_memory import AthosMemory
from athos_router import AthosRouter
from athos_engine import AthosEngine
from observability import process_snapshot, stop_observed_pid
from capabilities import status_report
from self_improvement import plan_self_improvement
from attach_protocol import attach_engine, attach_prompt, context_for_attach, delegate as delegate_request, report as attach_report
from named_protocols import run_protocol

STATIC       = Path(__file__).parent
ACCESS_TOKEN = config.ATHOS_ACCESS_TOKEN

# ── Singletons partagés ───────────────────────────────────────────────────────
_mem    = AthosMemory()
_router = AthosRouter(_mem)


def _make_loop_llm():
    """Return a blocking llm_call for the autonomous loop — uses best available engine."""
    def _call(prompt: str) -> str:
        # Prefer Anthropic API if key present and budget allows
        if config.ANTHROPIC_KEY and config.paid_api_allowed("anthropic"):
            try:
                import anthropic as _ant
                client = _ant.Anthropic(api_key=config.ANTHROPIC_KEY)
                msg = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text
            except Exception:
                pass
        # Fallback: claude CLI subprocess
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text", "--dangerously-skip-permissions"],
                capture_output=True, text=True, timeout=120, cwd=str(config.ATHOS_PATH),
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return "[loop_llm_unavailable]"
    return _call

# ── Permission prompts (bloquants) ────────────────────────────────────────────
_permits:      dict[str, dict] = {}
_permits_lock: threading.Lock  = threading.Lock()

def _make_permission_checker(sse_fn):
    def check(tool_name: str, inputs: dict) -> bool:
        perm_id = uuid.uuid4().hex
        evt     = threading.Event()
        with _permits_lock:
            _permits[perm_id] = {"event": evt, "approved": False}
        sse_fn({"permission_required": True, "id": perm_id,
                "tool": tool_name, "inputs": {k: str(v)[:200] for k, v in inputs.items()}})
        evt.wait(timeout=60)
        with _permits_lock:
            result = _permits.pop(perm_id, {})
        return result.get("approved", False)
    return check

# ── Threading HTTP ────────────────────────────────────────────────────────────
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── Handler ───────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/session":
            if not self._auth(): return
            self._json(session_kernel.status()); return

        if p == "/api/attach_prompt":
            if not self._auth(): return
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown;charset=utf-8")
            self.cors(); self.end_headers()
            self.wfile.write(attach_prompt().encode("utf-8")); return

        routes = {"/": "index.html", "/index.html": "index.html",
                  "/manifest.json": "manifest.json",
                  "/icon-192.png": "icon-192.png", "/icon-512.png": "icon-512.png"}
        name = routes.get(p)
        f    = STATIC / name if name else None
        if not f or not f.exists():
            self.send_response(404); self.end_headers(); return
        mime = {".html": "text/html;charset=utf-8", ".json": "application/json;charset=utf-8", ".png": "image/png"}
        self.send_response(200)
        self.send_header("Content-Type", mime.get(f.suffix, "text/plain"))
        self.cors(); self.end_headers()
        self.wfile.write(f.read_bytes())

    def _body(self) -> dict:
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.cors(); self.end_headers(); self.wfile.write(body)

    def _auth(self) -> bool:
        if request_authorized(self.headers, ACCESS_TOKEN): return True
        self._json({"error": "unauthorized", "auth_required": True}, 401); return False

    def do_POST(self):
        p = self.path
        if p.startswith("/api/") and not self._auth(): return

        # ── Status ──────────────────────────────────────────────────────────
        if p == "/api/status":
            s = _router.status()
            self._json({**s, "session": session_kernel.status()}); return

        if p == "/api/observability":
            from agent import list_processes
            self._json(process_snapshot(list_processes())); return

        if p == "/api/capabilities":
            self._json({
                "text": status_report(),
                "session": session_kernel.status(),
                "sync": sync_manager.status(),
            }); return

        if p == "/api/attach":
            self._json(attach_engine(self._body())); return

        if p == "/api/context_pack":
            self._json(context_for_attach(self._body())); return

        if p == "/api/delegate":
            self._json(delegate_request(self._body())); return

        if p == "/api/report":
            self._json(attach_report(self._body())); return

        if p == "/api/checkpoint":
            body = self._body()
            self._json(session_kernel.checkpoint(
                body.get("goal", "checkpoint Athos"),
                decisions=body.get("decisions", []),
                tasks=body.get("tasks", []),
                files=body.get("files", []),
            )); return

        if p == "/api/protocol":
            body = self._body()
            self._json(run_protocol(body.get("name", ""), body)); return

        if p == "/api/sync/status":
            self._json(sync_manager.status()); return

        if p == "/api/sync/queue":
            body = self._body()
            self._json(sync_manager.queue_job(
                body.get("kind", "manual"),
                payload=body.get("payload", {}),
                requires_network=bool(body.get("requires_network", True)),
                source=body.get("source", "api"),
            )); return

        if p == "/api/sync/run":
            self._json(sync_manager.run_once()); return

        if p == "/api/self_improvement_plan":
            body = self._body()
            self._json({"plan": plan_self_improvement(body.get("request", "")).to_dict()}); return

        # ── Alertes ─────────────────────────────────────────────────────────
        if p == "/api/budget_alert":
            self._json(_mem.pop_alert("budget_alert.json")); return
        if p == "/api/engine_alert":
            self._json(_mem.pop_alert("engine_alert.json")); return

        # ── Stream principal (SSE) ───────────────────────────────────────────
        if p == "/api/stream":
            msg = self._body().get("message", "")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control",  "no-cache")
            self.cors(); self.end_headers()
            stream_open = True

            def sse(obj):
                nonlocal stream_open
                if not stream_open:
                    return False
                try:
                    self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode())
                    self.wfile.flush()
                    return True
                except (BrokenPipeError, ConnectionResetError, OSError):
                    stream_open = False
                    return False

            try:
                athos = AthosEngine(_mem, _router, sse, lambda: _make_permission_checker(sse))
                reply = athos.respond(msg)
                if reply:
                    extract_and_save_async(msg, reply)
            except Exception as e:
                sse({"error": str(e), "t": f"Erreur : {e}"})

            sse("[DONE]"); return

        # ── Transcription audio (STT serveur) ────────────────────────────────
        if p == "/api/transcribe":
            length     = int(self.headers.get("Content-Length", 0))
            audio_bytes = self.rfile.read(length)
            if not audio_bytes:
                self._json({"error": "no audio"}, 400); return
            import speech_recognition as sr
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes); tmp_path = tmp.name
            wav_path = tmp_path.replace(".webm", ".wav")
            try:
                if not shutil.which("ffmpeg"):
                    self._json({"error": "ffmpeg manquant: installe `brew install ffmpeg` pour le fallback vocal serveur."}, 500)
                    return
                conv = subprocess.run(["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path],
                                      capture_output=True, text=True, timeout=30)
                if conv.returncode != 0:
                    self._json({"error": f"conversion audio impossible: {conv.stderr[-240:]}"}, 500)
                    return
                rec = sr.Recognizer()
                with sr.AudioFile(wav_path) as src:
                    audio = rec.record(src)
                if config.OPENAI_KEY and config.spend_policy()["whisper_enabled"]:
                    import openai
                    with open(wav_path, "rb") as f:
                        text = openai.OpenAI(api_key=config.OPENAI_KEY).audio.transcriptions.create(
                            model="whisper-1", file=f, language="fr").text
                else:
                    text = rec.recognize_google(audio, language="fr-FR")
                self._json({"text": text})
            except Exception as e:
                self._json({"error": str(e)}, 500)
            finally:
                for f in [tmp_path, wav_path]:
                    try: Path(f).unlink()
                    except: pass
            return

        # ── Process control ──────────────────────────────────────────────────
        if p == "/api/kill":
            body = self._body()
            pid  = body.get("pid")
            if pid:
                from agent import kill_process
                self._json({"ok": True, "msg": kill_process(int(pid))}); return
            self._json({"ok": False, "msg": "pid manquant"}, 400); return

        if p == "/api/stop_observed":
            body = self._body()
            pid = body.get("pid")
            if pid:
                self._json({"ok": True, "msg": stop_observed_pid(int(pid))}); return
            self._json({"ok": False, "msg": "pid manquant"}, 400); return

        if p == "/api/permit":
            body    = self._body()
            perm_id = body.get("id", "")
            approved = bool(body.get("approved", False))
            with _permits_lock:
                entry = _permits.get(perm_id)
            if entry:
                entry["approved"] = approved; entry["event"].set()
                self._json({"ok": True, "approved": approved}); return
            self._json({"ok": False, "msg": "permission introuvable"}, 404); return

        if p == "/api/processes":
            from agent import list_processes
            self._json({"processes": list_processes()}); return

        # ── AGI cognition endpoints ──────────────────────────────────────────
        if p == "/api/goals":
            from goal_manager import get_manager
            body = self._body()
            gm = get_manager()
            action = body.get("action", "list")
            if action == "add":
                g = gm.add(
                    description=body.get("description", ""),
                    priority=int(body.get("priority", 5)),
                    steps=body.get("steps", []),
                    source=body.get("source", "user"),
                )
                self._json(g.to_dict()); return
            if action == "clear_done":
                self._json({"cleared": gm.clear_done()}); return
            if action == "fail":
                g = gm.get(body.get("id", ""))
                if g:
                    g.fail(body.get("reason", "user request"))
                    gm.update(g)
                    self._json(g.to_dict()); return
            self._json({
                "goals": [g.to_dict() for g in gm.list_all()],
                "summary": gm.status_summary(),
                "top": gm.top().to_dict() if gm.top() else None,
            }); return

        if p == "/api/beliefs":
            from belief_store import get_store
            body = self._body()
            bs = get_store()
            action = body.get("action", "query")
            if action == "add":
                b = bs.add(
                    subject=body.get("subject", ""),
                    predicate=body.get("predicate", ""),
                    confidence=float(body.get("confidence", 0.8)),
                    source=body.get("source", "user"),
                    tags=body.get("tags", []),
                    ttl_seconds=body.get("ttl_seconds"),
                    verified=bool(body.get("verified", False)),
                )
                self._json(b.to_dict()); return
            if action == "forget":
                self._json({"ok": bs.forget(body.get("id", ""))}); return
            beliefs = bs.query(
                subject=body.get("subject"),
                tag=body.get("tag"),
                min_confidence=float(body.get("min_confidence", 0.0)),
            )
            self._json({
                "beliefs": [b.to_dict() for b in beliefs],
                "summary": bs.summary(),
            }); return

        if p == "/api/skills":
            from skill_library import get_library
            body = self._body()
            lib = get_library()
            action = body.get("action", "list")
            if action == "propose":
                s = lib.propose(
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                    code=body.get("code", ""),
                    dependencies=body.get("dependencies", []),
                    tags=body.get("tags", []),
                    test_code=body.get("test_code", ""),
                    source_repo=body.get("source_repo", ""),
                )
                self._json(s.to_dict()); return
            if action == "integrate":
                ok, msg = lib.test_and_integrate(
                    body.get("id", ""),
                    allow_mutation=bool(body.get("allow_mutation", False)),
                    allow_dependency_install=bool(body.get("allow_dependency_install", False)),
                )
                self._json({"ok": ok, "msg": msg}); return
            if action == "plan":
                self._json(lib.integration_plan(body.get("id", ""))); return
            if action == "search":
                results = lib.search(body.get("query", ""), limit=int(body.get("limit", 5)))
                self._json({"skills": [s.to_dict() for s in results]}); return
            self._json({
                "skills": [s.to_dict() for s in lib.list_active()],
                "summary": lib.summary(),
            }); return

        if p == "/api/search":
            from tools.web_search import search, search_github, fetch_raw
            body = self._body()
            kind = body.get("kind", "web")
            query = body.get("query", "")
            if kind == "github":
                self._json({"results": search_github(query, max_results=int(body.get("max_results", 5)))}); return
            if kind == "fetch":
                self._json({"content": fetch_raw(body.get("url", ""))}); return
            self._json({"results": search(query, max_results=int(body.get("max_results", 5)))}); return

        if p == "/api/loop":
            from autonomous_loop import recent_events, start_loop, status as loop_status, stop_loop
            body = self._body()
            action = body.get("action", "status")
            if action == "start":
                try:
                    start_loop(
                        _make_loop_llm(),
                        tick_interval=float(body.get("tick_interval", config.AUTONOMOUS_LOOP_DEFAULT_TICK)),
                        idle_stop_after=int(body.get("idle_stop_after", 0)),
                        allow_autonomous=bool(body.get("allow_autonomous", False)),
                        allow_skill_mutation=bool(body.get("allow_skill_mutation", False)),
                    )
                except PermissionError as e:
                    self._json({"ok": False, "running": False, "requires_confirmation": True, "msg": str(e), "status": loop_status()}); return
                self._json({"ok": True, **loop_status()}); return
            if action == "stop":
                stop_loop()
                self._json({"ok": True, **loop_status()}); return
            if action == "events":
                self._json({"events": recent_events(limit=int(body.get("limit", 20))), "status": loop_status()}); return
            self._json(loop_status()); return

        self.send_response(404); self.end_headers()


if __name__ == "__main__":
    port = 7474
    s    = _router.status()
    print(f"\n  ╔══════════════════════════════════╗")
    print(f"  ║      A.T.H.O.S. — VOICE SERVER   ║")
    print(f"  ╚══════════════════════════════════╝\n")
    print(f"  Moteur  : {s['engine'].upper()}")
    print(f"  Budget  : {s['budget']:.2f}€")
    print(f"  Port    : {port}\n")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
