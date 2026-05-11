"""
AthosEngine — cerveau unifié d'ATHOS.

Pattern : super-LLM X qui englobe A, B, C (ChatGPT, Claude, Grok, Ollama),
leurs contextes, leurs compétences et leur failover.

Point d'entrée unique : AthosEngine(mem, router).respond(msg)
"""
import json
import subprocess
import threading
import urllib.request
import urllib.error

try:
    from . import config, engine_router, session_kernel
    from .capabilities import matches_self_knowledge_request, status_report
    from .reasoning_kernel import build_frame
    from .self_improvement import matches_self_improvement_request, plan_self_improvement
    from .named_protocols import match_protocol, run_protocol
    from .athos_memory import AthosMemory
    from .athos_router import AthosRouter
    from .goal_manager import get_manager as get_goal_manager
    from .belief_store import get_store as get_belief_store
    from .skill_library import get_library as get_skill_library
except ImportError:
    import config
    import engine_router
    import session_kernel
    from capabilities import matches_self_knowledge_request, status_report
    from reasoning_kernel import build_frame
    from self_improvement import matches_self_improvement_request, plan_self_improvement
    from named_protocols import match_protocol, run_protocol
    from athos_memory import AthosMemory
    from athos_router import AthosRouter
    from goal_manager import get_manager as get_goal_manager
    from belief_store import get_store as get_belief_store
    from skill_library import get_library as get_skill_library

CHATGPT_LIMIT_MARKERS = ["usage limit", "upgrade to pro", "purchase more credits"]

ENGINE_LABELS = {
    "chatgpt_plus":  "Athos via ChatGPT Plus CLI",
    "claude_code":   "Athos via Claude Code Pro",
    "anthropic_api": "Athos via Anthropic API",
    "grok":          "Athos via Grok",
    "ollama":        "Athos via Ollama local",
}


class AthosEngine:
    def __init__(self, mem: AthosMemory, router: AthosRouter, sse, make_permission_checker):
        self.mem    = mem
        self.router = router
        self.sse    = sse
        self._make_perm = make_permission_checker

    # ── Callbacks internes ────────────────────────────────────────────────────

    def _bubble(self, text: str):
        self.sse({"t": text})

    def _terminal(self, line: str):
        self.sse({"toolbus": "stderr", "chunk": line, "pid": 0})

    def _thinking(self, kind: str, text: str):
        self.sse({"thinking": {"kind": kind, "text": text}})

    def _action(self, name, inputs, result, engine):
        label = (inputs.get("command") or inputs.get("script", "")
                 or inputs.get("query", "") or name)[:60]
        session_kernel.record_action(name, label, str(result)[:200], engine=engine)
        self.sse({"action": name, "label": label, "result": str(result)[:200]})

    def _toolbus(self, event_type, data):
        self.sse({"toolbus": event_type, **data})

    def _record(self, msg, reply, engine):
        self.mem.push("user", msg)
        self.mem.push("assistant", reply)
        self.mem.save_exchange(msg, reply)
        self.mem.log_exchange(msg, reply, engine)
        session_kernel.record_exchange(msg, reply, engine)

    def _local_reply(self, msg: str) -> str | None:
        protocol = match_protocol(msg)
        if protocol:
            return run_protocol(protocol, {"request": msg}).get("text", "")
        if matches_self_knowledge_request(msg):
            return status_report()
        if matches_self_improvement_request(msg):
            return plan_self_improvement(msg).as_text()
        return None

    def _call_engine(self, engine: str, msg: str) -> str:
        if engine in config.FAILOVER_TEST_ENGINES:
            raise RuntimeError(f"Failover test demandé pour {engine}")
        if engine == "chatgpt_plus":
            reply = self._chatgpt_plus(msg)
            self._bubble(reply)
            return reply
        if engine == "claude_code":
            reply = self._claude_code(msg)
            self._bubble(reply)
            return reply
        if engine in ("anthropic_api", "claude"):
            reply = self._anthropic_api(msg, engine)
            self._bubble(reply)
            return reply
        if engine == "grok":
            return self._grok(msg)
        if engine == "ollama":
            return self._ollama(msg)
        raise RuntimeError(f"Moteur inconnu : {engine}")

    # ── Engines ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(system: str, ctx: str, history: list, msg: str) -> str:
        """Identité ATHOS complète + contexte mémoire + cognition AGI + historique + message."""
        parts = [system]
        if ctx:
            parts.append(f"CONTEXTE MÉMOIRE:\n{ctx}")
        # AGI cognition context
        try:
            beliefs_ctx = get_belief_store().context_for(msg, limit=5)
            if beliefs_ctx:
                parts.append(beliefs_ctx)
        except Exception:
            pass
        try:
            skills_ctx = get_skill_library().context_for_llm(limit=10)
            if skills_ctx and "Aucun" not in skills_ctx:
                parts.append(skills_ctx)
        except Exception:
            pass
        try:
            gm = get_goal_manager()
            top = gm.top()
            if top:
                parts.append(f"OBJECTIF ACTIF: [{top.priority}] {top.description} (step {top.current_step}/{len(top.steps)})")
        except Exception:
            pass
        if history:
            hist_lines = "\n".join(
                f"{m['role'].upper()}: {m['content'][:300]}"
                for m in history[-6:]
            )
            parts.append(f"HISTORIQUE RÉCENT:\n{hist_lines}")
        parts.append(f"USER: {msg}")
        return "\n\n".join(parts)

    def _chatgpt_plus(self, msg: str) -> str:
        from agent import SYSTEM
        prompt = self._build_prompt(SYSTEM, self.mem.context(), self.mem.get_history(), msg)
        codex  = engine_router.chatgpt_plus_path()
        if not codex:
            raise RuntimeError("ChatGPT Plus CLI introuvable")
        result = subprocess.run(
            [codex, "exec", "--dangerously-bypass-approvals-and-sandbox", prompt],
            capture_output=True, text=True, timeout=180, cwd=str(config.ATHOS_PATH),
        )
        for line in result.stderr.strip().splitlines():
            if line: self._terminal(line)
        combined = result.stdout + result.stderr
        if result.returncode != 0 or any(m in combined.lower() for m in CHATGPT_LIMIT_MARKERS):
            raise RuntimeError(f"ChatGPT Plus limite : {combined[:120]}")
        return result.stdout.strip()

    def _claude_code(self, msg: str) -> str:
        from agent import SYSTEM
        prompt = self._build_prompt(SYSTEM, self.mem.context(), self.mem.get_history(), msg)
        proc   = subprocess.Popen(
            ["claude", "-p", prompt, "--output-format", "text", "--dangerously-skip-permissions"],
            cwd=str(config.ATHOS_PATH),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
        )
        def drain():
            for line in proc.stderr:
                if line.rstrip(): self._terminal(line.rstrip())
        threading.Thread(target=drain, daemon=True).start()
        output = proc.stdout.read()
        proc.wait(timeout=180)
        if not output.strip() or proc.returncode != 0:
            raise RuntimeError(f"Claude Code échec (code {proc.returncode})")
        return output.strip()

    def _anthropic_api(self, msg: str, engine: str) -> str:
        if not config.paid_api_allowed("anthropic"):
            raise RuntimeError("Anthropic API désactivée par la politique zéro dépense")
        from agent import run_agent, SYSTEM
        ctx    = self.mem.context()
        system = SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")
        draft  = run_agent(
            msg, system, self.mem.get_history(), config.ANTHROPIC_KEY,
            on_action=lambda n, i, r: self._action(n, i, r, engine),
            on_stream=self._toolbus,
            permission_check=self._make_perm(),
        )
        if not draft.startswith("▶") and len(draft) > 80:
            from quality import quality_pipeline
            draft = quality_pipeline(
                msg, draft, system, config.ANTHROPIC_KEY,
                lambda s: self.sse({"action": "quality", "label": s, "result": ""}),
            )
        self.mem.track_usage(len(msg) // 4 + 300, len(draft) // 4)
        return draft

    def _grok(self, msg: str) -> str:
        from agent import SYSTEM
        ctx  = self.mem.context()
        msgs = ([{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
                + self.mem.get_history()
                + [{"role": "user", "content": msg}])
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
                    if t: full += t; self._bubble(t)
                except Exception: continue
        return full

    def _ollama(self, msg: str) -> str:
        from agent import SYSTEM
        ctx   = self.mem.context()
        model = self.router.best_ollama_model()
        msgs  = ([{"role": "system", "content": SYSTEM + (f"\n\nCONTEXTE:\n{ctx}" if ctx else "")}]
                 + self.mem.get_history()
                 + [{"role": "user", "content": msg}])
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
                    if t: full += t; self._bubble(t)
                    if chunk.get("done"): break
                except Exception: continue
        return full

    def _async_gap_check(self, reply: str) -> None:
        """Fire-and-forget: detect skill gap in reply and acquire in background."""
        def _run():
            try:
                from skill_acquisition import scan_and_acquire
            except ImportError:
                try:
                    from .skill_acquisition import scan_and_acquire
                except ImportError:
                    return
            try:
                from server import _make_loop_llm  # reuse same llm factory
                skill = scan_and_acquire(reply, _make_loop_llm())
                if skill:
                    self.sse({"action": "skill_acquired", "label": skill.name,
                              "result": skill.description})
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    # ── Point d'entrée unique ─────────────────────────────────────────────────

    def respond(self, msg: str) -> str:
        attempted: set[str] = set()
        available = self.router.available()
        frame = build_frame(msg, available, self.router.current)
        for event in frame.events():
            self.sse(event)

        local = self._local_reply(msg)
        if local is not None:
            self._bubble(local)
            self._record(msg, local, "athos_kernel")
            return local

        engine = self.router.current
        session_kernel.checkpoint(
            goal=msg[:240],
            decisions=["contexte sauvegardé avant tentative moteur"],
            tasks=[f"moteur initial: {engine}", "reprendre avec le moteur suivant si limite/erreur"],
            files=[],
        )

        while engine not in attempted:
            attempted.add(engine)
            self.sse({"action": engine, "label": ENGINE_LABELS.get(engine, engine), "result": ""})

            try:
                reply = self._call_engine(engine, msg)
                self._record(msg, reply, engine)
                session_kernel.record_summary(
                    f"Demande traitée via {engine}; fallback attempts={len(attempted)-1}; objectif={msg[:180]}",
                    source="athos_engine",
                )
                self._async_gap_check(reply)
                return reply

            except urllib.error.HTTPError as e:
                if e.code in (402, 413, 429, 529):
                    next_eng = self.router.degrade(f"HTTP {e.code}")
                    session_kernel.checkpoint(
                        goal=msg[:240],
                        decisions=[f"{engine} indisponible HTTP {e.code}", f"bascule vers {next_eng}"],
                        tasks=["reprendre la même demande avec le même contexte"],
                        files=[],
                    )
                    self.sse({"action": "failover", "label": f"{engine} → {next_eng}", "result": f"HTTP {e.code}"})
                    if next_eng == "none": self._bubble("Aucun moteur disponible."); return ""
                    engine = next_eng; continue
                self._bubble(f"Erreur API : {e.code}"); return ""

            except RuntimeError as e:
                next_eng = self.router.degrade(str(e)[:80])
                session_kernel.record_action("failover", f"{engine} → {next_eng}", str(e)[:200], engine=engine)
                session_kernel.checkpoint(
                    goal=msg[:240],
                    decisions=[f"{engine} indisponible: {str(e)[:120]}", f"bascule vers {next_eng}"],
                    tasks=["reprendre la même demande avec le même contexte"],
                    files=[],
                )
                self.sse({"action": "failover", "label": f"{engine} → {next_eng}", "result": str(e)[:80]})
                if next_eng == "none": self._bubble("Aucun moteur disponible."); return ""
                engine = next_eng; continue

            except Exception as e:
                self._terminal(f"[{engine}] erreur inattendue : {e}")
                self._bubble(f"Erreur : {e}"); return ""

        self._bubble("Aucun moteur disponible."); return ""
