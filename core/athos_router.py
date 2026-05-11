"""
AthosRouter — gestion de l'engine actif et du failover.

Encapsule : détection des engines disponibles, état courant, dégradation.
"""
import urllib.request
import json

try:
    from . import config, engine_router
    from .athos_memory import AthosMemory
except ImportError:
    import config
    import engine_router
    from athos_memory import AthosMemory


class AthosRouter:
    def __init__(self, memory: AthosMemory):
        self._mem     = memory
        self.current  = "none"
        self.degraded = False
        self.current  = self._detect()

    # ── Détection ─────────────────────────────────────────────────────────────

    def _ollama_models(self) -> list:
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
                return [m["name"] for m in json.loads(r.read()).get("models", [])]
        except Exception:
            return []

    def best_ollama_model(self) -> str:
        priority  = ["llama3.2:1b", "llama3.2", "phi3:mini", "mistral"]
        available = self._ollama_models()
        for want in priority:
            for name in available:
                if name == want or name.startswith(want):
                    return name
        return available[0] if available else "mistral"

    def available(self) -> list[str]:
        return engine_router.available_engines(
            anthropic_key   = config.ANTHROPIC_KEY,
            openai_key      = config.OPENAI_KEY,
            openai_enabled  = config.OPENAI_ENABLED and config.paid_api_allowed("openai"),
            anthropic_enabled = config.paid_api_allowed("anthropic"),
            grok_key        = config.GROK_KEY,
            has_ollama      = lambda: bool(self._ollama_models()),
            has_chatgpt_plus= engine_router.chatgpt_plus_available,
            has_claude_code = engine_router.claude_code_available,
        )

    def _detect(self) -> str:
        return engine_router.first_available(self.available())

    # ── Failover ──────────────────────────────────────────────────────────────

    def degrade(self, reason: str) -> str:
        engines = self.available()
        if not engines:
            self.current  = "none"
            self.degraded = True
            return "none"
        next_eng = engine_router.next_engine(self.current, engines)
        if next_eng == self.current:
            return next_eng
        self.current  = next_eng
        self.degraded = True
        self._mem.notify("A.T.H.O.S.", f"Basculé {next_eng.upper()} : {reason}", "Basso")
        self._mem.write_alert("engine_alert.json", {
            "alert":  True,
            "engine": next_eng,
            "msg":    f"Je suis passé sur {next_eng.upper()}, Clément.",
        })
        return next_eng

    def status(self) -> dict:
        b = self._mem.load_budget()
        return {
            "engine":    self.current,
            "degraded":  self.degraded,
            "available": self.available(),
            "budget":    round(b.get("total_eur", 0.0), 4),
            "spend_policy": config.spend_policy(),
        }
