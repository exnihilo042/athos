"""
AthosMemory — mémoire unifiée d'ATHOS.

Encapsule : historique session, contexte Drive, échanges, logs, budget.
Source unique de vérité pour tout ce qui touche à la mémoire.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from . import config, session_kernel
except ImportError:
    import config
    import session_kernel

PRICE_IN   = 3e-6
PRICE_OUT  = 15e-6
ALERT_STEP = 1.0


class AthosMemory:
    def __init__(self):
        self._history:    list[dict] = []
        self._drive       = config.DRIVE
        self._budget_file = config.ATHOS_PATH / "budget.json"
        self._static      = config.ATHOS_PATH / "voice"
        self._load_history()

    # ── Historique ────────────────────────────────────────────────────────────

    def _load_history(self):
        msgs = session_kernel.latest_messages(limit=12)
        if msgs:
            self._history.extend(msgs)
            return
        f = self._drive / "athos_conv.mem"
        if not f.exists():
            return
        lines = f.read_text("utf-8").splitlines()
        for line in [l for l in lines if l.startswith("§conv:")][-12:]:
            parts = line.split("|")
            u = parts[1].split(":", 1)[1] if len(parts) > 1 else ""
            a = parts[2].split(":", 1)[1] if len(parts) > 2 else ""
            if u: self._history.append({"role": "user",      "content": u})
            if a: self._history.append({"role": "assistant", "content": a})
        while len(self._history) > 12:
            self._history.pop(0)

    def push(self, role: str, content: str):
        self._history.append({"role": role, "content": content})
        while len(self._history) > 12:
            self._history.pop(0)

    def get_history(self) -> list[dict]:
        return list(self._history)

    # ── Contexte ──────────────────────────────────────────────────────────────

    def context(self) -> str:
        parts = []
        kernel_ctx = session_kernel.context_pack(max_chars=1200)
        if kernel_ctx:
            parts.append(kernel_ctx)
        for fname, keys in [
            ("athos_identity.mem", ["§id:", "§user:", "§agency:"]),
            ("athos_projects.mem", ["status:active", "next:", "blocker:"]),
            ("athos_conv.mem",     ["§conv:"]),
        ]:
            f = self._drive / fname
            if not f.exists():
                continue
            lines = f.read_text("utf-8").splitlines()
            selected = (
                [l for l in lines if l.startswith("§conv:")][-8:]
                if fname == "athos_conv.mem"
                else [l for l in lines if any(k in l for k in keys)][:6]
            )
            if selected:
                parts.append("\n".join(selected))
        return "\n".join(parts)[:1800]

    # ── Persistance échanges ──────────────────────────────────────────────────

    def save_exchange(self, user: str, reply: str):
        ts   = datetime.now().strftime("%m-%dT%H:%M")
        line = f"§conv:{ts}|u:{user[:80].replace('|','/')}|a:{reply[:120].replace('|','/')}"
        try:
            f     = self._drive / "athos_conv.mem"
            lines = f.read_text("utf-8").splitlines() if f.exists() else []
            lines = [l for l in lines if l.startswith("§conv:")][-20:]
            lines.append(line)
            f.write_text("\n".join(lines) + "\n", "utf-8")
        except Exception:
            pass

    def log_exchange(self, user: str, reply: str, engine: str):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            ts    = datetime.now().strftime("%H:%M")
            entry = f"§voice:{ts}|eng:{engine}|u:{user[:80].replace('|','/')}|a:{reply[:150].replace('|','/')}\n"
            log_f = self._drive / "logs" / f"{today}.mem"
            log_f.parent.mkdir(exist_ok=True)
            with open(log_f, "a", encoding="utf-8") as lf:
                lf.write(entry)
        except Exception:
            pass

    # ── Budget ────────────────────────────────────────────────────────────────

    def load_budget(self) -> dict:
        try:
            return json.loads(self._budget_file.read_text()) if self._budget_file.exists() else {}
        except Exception:
            return {}

    def track_usage(self, in_tok: int, out_tok: int):
        b = {**{"total_eur": 0.0, "last_alert_at": 0.0, "requests": 0}, **self.load_budget()}
        b["total_eur"] += (in_tok * PRICE_IN + out_tok * PRICE_OUT) * 0.92
        b["requests"]  += 1
        if b["total_eur"] >= b["last_alert_at"] + ALERT_STEP:
            b["last_alert_at"] = (b["total_eur"] // ALERT_STEP) * ALERT_STEP
            self._budget_file.write_text(json.dumps(b, indent=2))
            self.notify("A.T.H.O.S.", f"{b['total_eur']:.0f}€ consommés sur Anthropic.", "Ping")
            self.write_alert("budget_alert.json", {
                "alert": True, "total": round(b["total_eur"], 2),
                "msg":   f"Attention Clément, {b['total_eur']:.0f} euros consommés sur l'API.",
            })
        else:
            self._budget_file.write_text(json.dumps(b, indent=2))

    # ── Alertes & notifications ───────────────────────────────────────────────

    @staticmethod
    def notify(title: str, msg: str, sound: str = "Glass"):
        subprocess.Popen(
            ["osascript", "-e", f'display notification "{msg}" with title "{title}" sound name "{sound}"']
        )

    def write_alert(self, filename: str, data: dict):
        (self._static / filename).write_text(json.dumps(data))

    def pop_alert(self, filename: str) -> dict:
        f = self._static / filename
        if not f.exists():
            return {"alert": False}
        d = json.loads(f.read_text())
        f.unlink()
        return d
