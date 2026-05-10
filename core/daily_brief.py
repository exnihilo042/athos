"""Athos — Daily Brief | no API | lit la mémoire et formate"""
import sys, subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_manager import read

def extract(mem: str, prefix: str) -> list:
    """Extrait les lignes §prefix: d'un fichier mem"""
    return [l[len(prefix):].strip() for l in mem.splitlines() if l.startswith(prefix)]

def build_brief() -> str:
    identity = read("athos_identity.mem")
    projects = read("athos_projects.mem")
    feedback = read("athos_feedback.mem")

    date = datetime.now().strftime("%A %d %B %Y")

    proj_actifs = [l for l in projects.splitlines()
                   if l.startswith("§proj:") and "status:active" in l]
    proj_next   = [l for l in projects.splitlines()
                   if l.startswith("§proj:") and "next:" in l]
    blockers    = [l for l in projects.splitlines()
                   if "blocker" in l]

    lines = [
        f"  ATHOS — {date}",
        "",
    ]

    if proj_actifs:
        lines.append("  PROJETS ACTIFS :")
        for p in proj_actifs:
            lines.append(f"    {p.replace('§proj:', '').replace('|status:active', '')}")

    if proj_next:
        lines.append("")
        lines.append("  NEXT ACTIONS :")
        for p in proj_next:
            name = p.split("|")[0].replace("§proj:", "")
            nxt  = [x.replace("next:", "") for x in p.split("|") if x.startswith("next:")]
            if nxt:
                lines.append(f"    [{name}] → {nxt[0]}")

    if blockers:
        lines.append("")
        lines.append("  BLOCKERS :")
        for b in blockers:
            lines.append(f"    ⚠ {b}")

    lines += ["", "  ─────────────────────────────"]
    return "\n".join(lines)

def display(brief: str):
    safe = brief.replace("'", "\\'").replace('"', '\\"').replace("\\n", "\\\\n")
    script = f"""tell application "Terminal"
    do script "clear && printf '{brief}'"
    activate
end tell"""
    subprocess.run(["osascript", "-e", script])

if __name__ == "__main__":
    brief = build_brief()
    display(brief)
