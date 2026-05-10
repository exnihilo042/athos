"""Athos — Session Writer | hook Stop | no API required"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import read, write, read_session, clear_session, log_today
from mem_merge import append_unique

# Routing : préfixes § → fichier cible
ROUTING = {
    "athos_behaviors.mem": ["§behavior", "§pattern", "§habit", "§learned_behavior"],
    "athos_projects.mem":  ["§proj", "§project", "§blocker", "§milestone"],
    "athos_feedback.mem":  ["§rule", "§feedback", "§correction", "§validated"],
}

def route(notes: str) -> dict:
    """Distribue les lignes § vers le bon fichier selon préfixe"""
    buckets = {f: [] for f in ROUTING}
    for line in notes.splitlines():
        line = line.strip()
        if not line.startswith("§"):
            continue
        matched = False
        for filename, prefixes in ROUTING.items():
            if any(line.startswith(p) for p in prefixes):
                buckets[filename].append(line)
                matched = True
                break
        # Ligne non-routée → behaviors par défaut (catch-all)
        if not matched and line.startswith("§learned"):
            buckets["athos_behaviors.mem"].append(line)

    return buckets

def run():
    notes = read_session()
    if not notes or len(notes.strip()) < 5:
        return

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M")
    print(f"§athos:session_writer|t:{ts}|status:start")

    log_today(notes)

    buckets = route(notes)
    for filename, lines in buckets.items():
        if not lines:
            continue
        existing = read(filename)
        updated  = append_unique(existing, "\n".join(lines))
        if updated != existing:
            write(filename, updated)
            print(f"§updated:{filename}|lines:{len(lines)}")

    clear_session()
    print("§athos:session_writer|status:done")

if __name__ == "__main__":
    run()
