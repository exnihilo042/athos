"""ATHOS Voice Server — couche HTTP pure. Toute la logique est dans core/."""
import sys, json, subprocess, threading, uuid, tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

import config
import session_kernel
from auth import request_authorized
from memory_extractor import extract_and_save_async
from athos_memory import AthosMemory
from athos_router import AthosRouter
from athos_engine import AthosEngine
from observability import process_snapshot, stop_observed_pid
from capabilities import status_report
from self_improvement import plan_self_improvement

STATIC       = Path(__file__).parent
ACCESS_TOKEN = config.ATHOS_ACCESS_TOKEN

# ── Singletons partagés ───────────────────────────────────────────────────────
_mem    = AthosMemory()
_router = AthosRouter(_mem)

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
            self._json({"text": status_report(), "session": session_kernel.status()}); return

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

            def sse(obj):
                self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode())
                self.wfile.flush()

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
                subprocess.run(["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path],
                               capture_output=True, timeout=30)
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
