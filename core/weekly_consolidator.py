"""Athos — Weekly Consolidator | no API | dedup + merge §-format"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import read, write, LOGS
from mem_merge import merge

TARGETS = ["athos_behaviors.mem", "athos_projects.mem", "athos_feedback.mem"]

def collect_week() -> str:
    lines = []
    for i in range(7):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        p = LOGS / f"{d}.mem"
        if p.exists():
            lines.append(p.read_text("utf-8"))
    return "\n".join(lines)

def run():
    print("§athos:consolidator|status:start")
    week_logs = collect_week()

    if not week_logs.strip():
        print("§athos:consolidator|status:no_logs")
        return

    for filename in TARGETS:
        existing = read(filename)
        updated  = merge(existing, week_logs)
        if updated != existing:
            write(filename, updated)
            print(f"§consolidated:{filename}")

    print("§athos:consolidator|status:done")

if __name__ == "__main__":
    run()
