"""Athos — §-format merger | no API, pure Python"""

def parse(content: str) -> dict:
    """Parse §-format → dict[key → full_line]"""
    result = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or not line.startswith("§"):
            continue
        key = line.split(":")[0] + ":" + line.split(":")[1].split("|")[0] if ":" in line else line
        result[key] = line
    return result

def merge(base: str, incoming: str) -> str:
    """Merge incoming § lines into base — incoming wins on conflict"""
    base_map = parse(base)
    new_map  = parse(incoming)
    merged   = {**base_map, **new_map}
    header   = [l for l in base.splitlines() if l.startswith("#") or l.startswith("§v:") or l.startswith("§note:")]
    body     = [v for k, v in merged.items() if not any(v == h for h in header)]
    return "\n".join(header + body) + "\n"

def append_unique(base: str, incoming: str) -> str:
    """Ajoute les lignes § de incoming absentes de base"""
    existing = set(base.splitlines())
    new_lines = [l for l in incoming.splitlines() if l.strip().startswith("§") and l not in existing]
    return base.rstrip() + ("\n" + "\n".join(new_lines) if new_lines else "") + "\n"
