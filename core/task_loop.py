"""ATHOS task loop — bounded autonomous execution for Codex/Claude work.

This is not a hidden background daemon. It runs a visible, finite task plan,
reports every step to ATHOS Room, and stops cleanly on success, failure, risk,
timeout, or missing work.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MEMORY_DIR = ROOT / "memory"
DEFAULT_ATHOS_URL = "http://localhost:7474"
DEFAULT_ENV_FILE = ROOT / ".env"
RISKY_PATTERNS = (
    "rm -rf",
    "git push",
    "git reset",
    "git clean",
    "git checkout --",
    "force-with-lease",
    "npm install",
    "pnpm install",
    "pip install",
    "brew install",
    "curl | sh",
    "shopify theme push",
    "shopify product",
    "shutdown",
    "reboot",
)


def _read_env_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    prefix = f"{key}="
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or not line.startswith(prefix):
                continue
            return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        return ""
    return ""


def resolve_athos_token(env_file: Path | None = None) -> str:
    """Resolve the local ATHOS bearer token for live Room reporting."""
    return (
        os.environ.get("ATHOS_TOKEN", "").strip()
        or os.environ.get("ATHOS_ACCESS_TOKEN", "").strip()
        or _read_env_value(env_file or DEFAULT_ENV_FILE, "ATHOS_ACCESS_TOKEN")
    )


@dataclass
class StepResult:
    command: str
    returncode: int | None
    status: str
    output_tail: str = ""
    duration_s: float = 0.0


@dataclass
class TaskResult:
    task_id: str
    objective: str
    status: str
    steps: list[StepResult] = field(default_factory=list)
    stop_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "objective": self.objective,
            "status": self.status,
            "stop_reason": self.stop_reason,
            "steps": [
                {
                    "command": s.command,
                    "returncode": s.returncode,
                    "status": s.status,
                    "duration_s": round(s.duration_s, 3),
                    "output_tail": s.output_tail,
                }
                for s in self.steps
            ],
        }


class RoomReporter:
    def __init__(
        self,
        actor: str = "codex",
        athos_url: str | None = None,
        memory_dir: Path | None = None,
        timeout: float = 2.0,
    ) -> None:
        self.actor = actor
        self.athos_url = (athos_url or os.environ.get("ATHOS_URL") or DEFAULT_ATHOS_URL).rstrip("/")
        self.memory_dir = memory_dir or Path(os.environ.get("ATHOS_MEMORY_DIR", DEFAULT_MEMORY_DIR))
        self.timeout = timeout
        self.token = resolve_athos_token()

    def post(
        self,
        msg_type: str,
        content: str,
        task_id: str,
        status: str = "",
        files: list[str] | None = None,
        meta: dict | None = None,
    ) -> dict:
        payload = {
            "actor": self.actor,
            "type": msg_type,
            "content": content,
            "task_id": task_id,
            "status": status,
            "files": files or [],
            "meta": meta or {},
        }
        if self._post_live(payload):
            return {"ok": True, "mode": "live", "payload": payload}
        self._post_offline(payload)
        return {"ok": True, "mode": "offline", "payload": payload}

    def _post_live(self, payload: dict) -> bool:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.athos_url}/api/message",
            data=data,
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return 200 <= response.status < 300
        except (OSError, urllib.error.URLError, TimeoutError):
            return False

    def _post_offline(self, payload: dict) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        payload = dict(payload)
        payload["id"] = payload.get("id") or uuid.uuid4().hex[:12]
        payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        payload["offline"] = True
        file = self.memory_dir / f"room_offline_{time.strftime('%Y%m%d')}.jsonl"
        with file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def command_is_risky(command: str) -> bool:
    lowered = " ".join(str(command).lower().split())
    return any(pattern in lowered for pattern in RISKY_PATTERNS)


def _tail(text: str, limit: int = 1800) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_task_loop(
    objective: str,
    commands: Iterable[str],
    *,
    actor: str = "codex",
    task_id: str | None = None,
    cwd: str | Path | None = None,
    timeout: int = 120,
    allow_mutation: bool = False,
    dry_run: bool = False,
    reporter: RoomReporter | None = None,
) -> TaskResult:
    task_id = task_id or f"task-{uuid.uuid4().hex[:10]}"
    reporter = reporter or RoomReporter(actor=actor)
    workdir = Path(cwd or os.getcwd())
    commands = [str(c) for c in commands if str(c).strip()]
    result = TaskResult(task_id=task_id, objective=objective, status="running")

    reporter.post(
        "action",
        f"task loop start — {objective}",
        task_id,
        status="running",
        meta={"cwd": str(workdir), "commands": commands, "dry_run": dry_run},
    )

    if not commands:
        result.status = "blocked"
        result.stop_reason = "no_commands"
        reporter.post("error", "task loop blocked — no commands supplied", task_id, status="blocked")
        return result

    for index, command in enumerate(commands, start=1):
        if command_is_risky(command) and not allow_mutation:
            step = StepResult(command=command, returncode=None, status="blocked")
            result.steps.append(step)
            result.status = "blocked"
            result.stop_reason = "risky_command_requires_allow_mutation"
            reporter.post(
                "error",
                f"step {index} blocked — risky command requires --allow-mutation: {command}",
                task_id,
                status="blocked",
                meta={"step": index, "command": command},
            )
            break

        reporter.post(
            "action",
            f"step {index} start — {command}",
            task_id,
            status="running",
            meta={"step": index, "command": command},
        )
        if dry_run:
            step = StepResult(command=command, returncode=0, status="dry_run")
            result.steps.append(step)
            reporter.post("result", f"step {index} dry-run OK — {command}", task_id, status="dry_run")
            continue

        start = time.time()
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
        duration = time.time() - start
        output = _tail((completed.stdout or "") + ("\n" if completed.stdout and completed.stderr else "") + (completed.stderr or ""))
        status = "completed" if completed.returncode == 0 else "failed"
        step = StepResult(
            command=command,
            returncode=completed.returncode,
            status=status,
            output_tail=output,
            duration_s=duration,
        )
        result.steps.append(step)
        reporter.post(
            "result",
            f"step {index} {status} rc={completed.returncode} duration={duration:.2f}s\n{output}",
            task_id,
            status=status,
            meta={"step": index, "command": command, "returncode": completed.returncode},
        )
        if completed.returncode != 0:
            result.status = "failed"
            result.stop_reason = f"command_failed:{index}"
            break
    else:
        result.status = "completed"
        result.stop_reason = "all_steps_completed"

    reporter.post(
        "checkpoint",
        f"task loop stop — {result.status} — {result.stop_reason}",
        task_id,
        status=result.status,
        meta=result.to_dict(),
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded ATHOS task loop and report to ATHOS Room.")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--task-id")
    parser.add_argument("--actor", default="codex")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--allow-mutation", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--step", action="append", default=[], help="Shell command to run. Repeat for multiple steps.")
    args = parser.parse_args(argv)

    result = run_task_loop(
        args.objective,
        args.step,
        actor=args.actor,
        task_id=args.task_id,
        cwd=args.cwd,
        timeout=args.timeout,
        allow_mutation=args.allow_mutation,
        dry_run=args.dry_run,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
