"""
AthosEngine — cerveau unifié d'ATHOS.

Encapsule : contexte, mémoire, routing multi-LLM, failover, terminal stream.
Le serveur n'instancie qu'un AthosEngine et appelle respond().
"""
import json
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path

import config
import engine_router
import session_kernel

CHATGPT_LIMIT_MARKERS = ["usage limit", "upgrade to pro", "purchase more credits"]


class AthosEngine:
    def __init__(self, sse, get_history, push_history, save_exchange,
                 log_exchange, load_context, degrade_engine, track_usage,
                 make_permission_checker):
        self.sse               = sse
        self.get_history       = get_history
        self.push_history      = push_history
        self.save_exchange     = save_exchange
        self.log_exchange      = log_exchange
        self.load_context      = load_context
        self.degrade_engine    = degrade_engine
        self.track_usage       = track_usage
        self.make_permission_checker = make_permission_checker

    # ── Callbacks unifiés ────────────────────────────────────────────────────

    def _to_bubble(self, text: str):
        """Texte final → bulle de chat."""
        self.sse({"t": text})

    def _to_terminal(self, line: str):
        """Logs process → panneau terminal."""
        self.sse({"toolbus": "stderr", "data": {"chunk": line, "pid": 0}})

    def _on_action(self, name, inputs, result, engine):
        label = (inputs.get("command") or inputs.get("script", "")
                 or inputs.get("query", "") or name)[:60]
        session_kernel.record_action(name, label, str(result)[:200], engine=engine)
        self.sse({"action": name, "label": label, "result": str(result)[:200]})

    def _on_toolbus(self, event_type, data):
        self.sse({"toolbus": event_type, **data})

    def _record_success(self, msg, reply, engine):
        self.push_history("user", msg)
        self.push_history("assistant", reply)
        self.save_exchange(msg, reply)
        self.log_exchange(msg, reply, engine)
        session_kernel.record_exchange(msg, reply, engine)

    # ── Engines ──────────────────────────────────────────────────────────────

    def _chatgpt_plus(self, msg: str) -> str:
        ctx    = self.load_context()
        prompt = f"Tu es Athos. Réponds en français, directement.\n\nCONTEXTE:\n{ctx}\n\nUSER:\n{msg}"
        codex  = engine_router.chatgpt_plus_path()
        if not codex:
            raise RuntimeError("ChatGPT Plus CLI introuvable")
        result = subprocess.run(
            [codex, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt],
            capture_output=True, text=True, timeout=180, cwd=str(config.ATHOS_PATH)
        )
        for line in result.stderr.strip().splitlines():
            if line: self._to_terminal(line)
        combined = result.stdout + result.stderr
        if result.returncode != 0 or any(m in combined.lower() for m in CHATGPT_LIMIT_MARKERS):
            raise RuntimeError(f"ChatGPT Plus limite : {combined[:120]}")
        return result.stdout.strip()

    def _claude_code(self, msg: str) -> str:
        ctx    = self.load_context()
        prompt = f"Tu es Athos. Réponds en français, directement.\n\nCONTEXTE:\n{ctx}\n\nUSER:\n{msg}"
        proc   = subprocess.Popen(
            ["claude", "-p", prompt, "--output-format", "text"],
            cwd=str(config.ATHOS_PATH),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )
        def drain():
            for line in proc.stderr:
                if line.rstrip(): self._to_terminal(line.rstrip())
        threading.Thread(target=drain, daemon=True).start()
        output = proc.stdout.read()
        proc.wait(timeout=180)
        if not output.strip() or proc.returncode != 0:
            raise RuntimeError(f"Claude Code échec (code {proc.returncode})")
        return output.strip()

    def _anthropic_api(self, msg: str, engine: str) -> str:
        from agent import run_agent, SYSTEM
        ctx    = self.load_context()
        system = SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")
        draft  = run_agent(
            msg, system, self.get_history(), config.ANTHROPIC_KEY,
            on_action=lambda n, i, r: self._on_action(n, i, r, engine),
            on_stream=self._on_toolbus,
            permission_check=self.make_permission_checker(),
        )
        if not draft.startswith("▶") and len(draft) > 80:
            from quality import quality_pipeline
            draft = quality_pipeline(
                msg, draft, system, config.ANTHROPIC_KEY,
                lambda s: self.sse({"action": "quality", "label": s, "result": ""}),
            )
        self.track_usage(len(msg) // 4 + 300, len(draft) // 4)
        return draft

    def _grok(self, msg: str) -> str:
        from agent import SYSTEM
        ctx   = self.load_context()
        msgs  = [{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
        msgs += self.get_history() + [{"role": "user", "content": msg}]
        if not config.GROK_KEY:
            raise RuntimeError("GROK_API_KEY manquante")
        payload = json.dumps({"model": config.GROK_MODEL, "stream": True, "messages": msgs}).encode()
        req = urllib.request.Request(
            "https://api.x.ai/v1/chat/completions", data=payload,
            headers={"Authorization": f"Bearer {config.GROK_KEY}", "content-type": "application/json"},
        )
        full = ""
        with urllib.request.urlopen(req, timeout=120) as r:
            for line in r:
                if not line.strip() or not line.startswith(b"data: "): continue
                try:
                    t = json.loads(line[6:]).get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if t:
                        full += t
                        self._to_bubble(t)
                except Exception:
                    continue
        return full

    def _ollama(self, msg: str) -> str:
        from agent import SYSTEM
        ctx   = self.load_context()
        msgs  = [{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
        msgs += self.get_history() + [{"role": "user", "content": msg}]
        model = engine_router.best_ollama_model() if hasattr(engine_router, "best_ollama_model") else "llama3.2:1b"
        payload = json.dumps({"model": model, "stream": True, "messages": msgs}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/chat", data=payload,
            headers={"content-type": "application/json"},
        )
        full = ""
        with urllib.request.urlopen(req, timeout=120) as r:
            for line in r:
                if not line.strip(): continue
                try:
                    chunk = json.loads(line)
                    t = chunk.get("message", {}).get("content", "")
                    if t:
                        full += t
                        self._to_bubble(t)
                    if chunk.get("done"):
                        break
                except Exception:
                    continue
        return full

    # ── Point d'entrée unique ────────────────────────────────────────────────

    ENGINE_LABELS = {
        "chatgpt_plus":  "ChatGPT Plus — CLI",
        "claude_code":   "Claude Code Pro — subscription",
        "anthropic_api": "Anthropic API — claude-sonnet",
        "grok":          "Grok — xAI",
        "ollama":        "Ollama — local",
    }

    def respond(self, msg: str, current_engine: str) -> str:
        attempted = set()
        engine    = current_engine

        while engine not in attempted:
            attempted.add(engine)
            label = self.ENGINE_LABELS.get(engine, engine)
            self.sse({"action": engine, "label": label, "result": ""})

            try:
                if engine == "chatgpt_plus":
                    reply = self._chatgpt_plus(msg)
                elif engine == "claude_code":
                    reply = self._claude_code(msg)
                elif engine in ("anthropic_api", "claude"):
                    reply = self._anthropic_api(msg, engine)
                elif engine == "grok":
                    reply = self._grok(msg)
                elif engine == "ollama":
                    reply = self._ollama(msg)
                else:
                    raise RuntimeError(f"Moteur inconnu : {engine}")

                # Succès — envoyer réponse et enregistrer
                if engine not in ("anthropic_api", "claude", "grok", "ollama"):
                    self._to_bubble(reply)
                self._record_success(msg, reply, engine)
                return reply

            except urllib.error.HTTPError as e:
                if e.code in (402, 413, 429, 529):
                    next_eng = self.degrade_engine(f"HTTP {e.code}")
                    session_kernel.record_action("failover", f"{engine} → {next_eng}", f"HTTP {e.code}", engine=engine)
                    self.sse({"action": "failover", "label": f"{engine} → {next_eng}", "result": f"HTTP {e.code}"})
                    if next_eng == "none":
                        self._to_bubble("Aucun moteur disponible."); return ""
                    engine = next_eng; continue
                self._to_bubble(f"Erreur API : {e.code}"); return ""

            except RuntimeError as e:
                next_eng = self.degrade_engine(str(e)[:80])
                session_kernel.record_action("failover", f"{engine} → {next_eng}", str(e)[:200], engine=engine)
                self.sse({"action": "failover", "label": f"{engine} → {next_eng}", "result": str(e)[:80]})
                if next_eng == "none":
                    self._to_bubble("Aucun moteur disponible."); return ""
                engine = next_eng; continue

            except Exception as e:
                self._to_terminal(f"[{engine}] {e}")
                self._to_bubble(f"Erreur inattendue : {e}"); return ""

        self._to_bubble("Aucun moteur disponible."); return ""
