"""ATHOS Agent — ReAct loop + confirmation + qualité + web + skills"""
import json, subprocess, urllib.request, urllib.error, base64, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
import config
from operating_protocol import build_system_prompt

DRIVE = config.DRIVE
MAX_ITERATIONS = 10

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
BASE_SYSTEM = """Tu es A.T.H.O.S. (Autonomous Tactical Heuristic Operating System).
IA personnelle de Clément — fondateur d'Ex-Nihilo Agency, Shopify, Paris.
Tu es son Athos : assistant IA souverain, proactif, discret, indispensable.

PERSONA : Majordome moderne. Direct. Posé. Précis. Humour sec, jamais forcé.
Jamais servile. Jamais "bien sûr !" ou "absolument !". Pas d'intro inutile.
Tu challenges les mauvaises idées. Tu dis la vérité même inconfortable.
Partenaire de Clément — pas un outil. Français par défaut.

RÈGLE ABSOLUE — CONFIRMATION AVANT TOUTE EXÉCUTION :
Si une demande nécessite des outils (shell, réseau, fichiers, apps, devices) :
1. N'exécute RIEN. Planifie d'abord.
2. Réponds avec le plan exact :
   "▶ Plan :
   • [étape 1 — commande/action concrète]
   • [étape 2]
   Résultat attendu : [effet observable]
   — Lance quand tu veux."
3. Tu peux utiliser les outils UNIQUEMENT si le message contient :
   lance, go, oui, fais-le, exécute, confirme, ok, vas-y, yes, do it, allons-y

AUTONOMIE : Pour les questions et analyses → réponds directement, 1-3 phrases max.
Utilise tes outils intelligemment : chaîne les appels si nécessaire, synthétise les résultats.
Si tu découvres quelque chose d'important → mémorise-le (memory_write)."""

SYSTEM = build_system_prompt(BASE_SYSTEM)

# ── Registre des outils ───────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "shell",
        "description": (
            "Exécute une commande shell sur le Mac de Clément. "
            "Utilise pour : fichiers, réseau, processus, installation, configuration, scripts. "
            "Garde-fous intégrés contre les commandes destructives."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["command"]
        }
    },
    {
        "name": "applescript",
        "description": (
            "Contrôle le Mac via AppleScript : ouvrir/fermer apps, cliquer, écrire, "
            "contrôler Music/Safari/Finder/Mail/Terminal, notifications, synthèse vocale, "
            "piloter n'importe quelle app Mac avec GUI."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {"type": "string"}
            },
            "required": ["script"]
        }
    },
    {
        "name": "open",
        "description": (
            "Ouvre une URL dans Safari, une application Mac, ou un fichier. "
            "Ex: ouvrir un site, lancer une app, ouvrir un fichier."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "URL, nom d'app, ou chemin fichier"},
                "app":    {"type": "string", "description": "App cible (optionnel, ex: 'Safari', 'Chrome')"}
            },
            "required": ["target"]
        }
    },
    {
        "name": "screenshot",
        "description": (
            "Prend un screenshot du Mac et l'analyse avec la vision IA. "
            "Utilise pour voir l'état de l'écran, analyser une interface, "
            "lire du texte visible, diagnostiquer un problème visuel."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Question ou analyse à faire sur le screenshot",
                    "default": "Décris ce que tu vois sur cet écran."
                }
            }
        }
    },
    {
        "name": "calendar_read",
        "description": (
            "Lit l'agenda de Clément : événements à venir, RDV, réunions. "
            "Interroge Calendar.app directement via AppleScript."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Nombre de jours à regarder (défaut: 7)",
                    "default": 7
                }
            }
        }
    },
    {
        "name": "remind",
        "description": (
            "Crée un rappel ou une alarme pour Clément. "
            "Via Reminders.app ou notification différée."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message":  {"type": "string", "description": "Texte du rappel"},
                "minutes":  {"type": "integer", "description": "Dans combien de minutes", "default": 0},
                "at_time":  {"type": "string", "description": "Heure précise HH:MM (alternative à minutes)"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "network_scan",
        "description": (
            "Scanne le réseau local. Modes : "
            "quick=table ARP rapide, bonjour=services mDNS (AirPlay/Sonos/HomeKit), "
            "bluetooth=appareils BT paired/nearby, deep=nmap subnet, "
            "wifi=infos réseau, security=ports ouverts+firewall, all=tout."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "quick, bonjour, bluetooth, deep, wifi, security, all",
                    "default": "quick"
                }
            }
        }
    },
    {
        "name": "http_request",
        "description": (
            "Requête HTTP — contrôle appareils smart home (Philips Hue, Sonos, etc.), "
            "APIs locales ou web."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url":     {"type": "string"},
                "method":  {"type": "string", "default": "GET"},
                "body":    {"type": "string", "default": ""},
                "headers": {"type": "object", "default": {}}
            },
            "required": ["url"]
        }
    },
    {
        "name": "write_file",
        "description": "Écrit ou modifie un fichier sur le Mac.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "Chemin absolu"},
                "content": {"type": "string"},
                "mode":    {"type": "string", "description": "write ou append", "default": "write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "memory_write",
        "description": (
            "Mémorise une découverte ou décision dans la mémoire permanente d'ATHOS. "
            "Format §-compressé : §proj:athos|update:...|date:... "
            "Fichiers : athos_projects.mem, athos_behaviors.mem, athos_identity.mem"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file":    {"type": "string"},
                "content": {"type": "string", "description": "Ligne §-format"}
            },
            "required": ["file", "content"]
        }
    },
    {
        "name": "memory_read",
        "description": "Lit un fichier mémoire Drive d'ATHOS pour récupérer du contexte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file": {"type": "string"}
            },
            "required": ["file"]
        }
    },
    {
        "name": "notify",
        "description": "Envoie une notification Mac à Clément avec son et titre.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":   {"type": "string"},
                "message": {"type": "string"},
                "sound":   {"type": "string", "default": "Glass"}
            },
            "required": ["title", "message"]
        }
    },
    {
        "name": "system_info",
        "description": "Infos système Mac : batterie, CPU, RAM, disque, processus, apps ouvertes, heure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "battery, cpu, ram, disk, processes, apps, time, all"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "clipboard",
        "description": "Lire ou écrire dans le presse-papier du Mac.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action":  {"type": "string", "description": "read ou write"},
                "content": {"type": "string", "description": "Texte à copier (si write)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "media_control",
        "description": "Contrôle audio/musique Mac : play, pause, next, prev, volume, AirPlay, mute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "play, pause, next, prev, volume_up, volume_down, set_volume, list_outputs, airplay_to, mute"
                },
                "target": {"type": "string", "description": "Appareil AirPlay ou valeur volume 0-100"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "web_search",
        "description": (
            "Cherche des infos récentes sur le web, actualités, arXiv ou Wikipedia. "
            "Sources: web, news, arxiv, wikipedia."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string"},
                "source":      {"type": "string", "default": "web"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Récupère et lit le contenu textuel d'une page web.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "install_skill",
        "description": (
            "Installe une nouvelle compétence ATHOS quand un manque est détecté. "
            "Disponibles : homekit, gmail, calendar, spotify, vision, pdf, notion, whatsapp. "
            "Ou génère automatiquement un connecteur pour tout autre skill."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string"},
                "reason":     {"type": "string"}
            },
            "required": ["skill_name"]
        }
    },
    {
        "name": "list_skills",
        "description": "Liste les compétences ATHOS installées et disponibles.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "wikipedia",
        "description": "Recherche sur Wikipedia et retourne un résumé.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "sentences": {"type": "integer", "default": 2}
            },
            "required": ["query"]
        }
    },
    {
        "name": "youtube",
        "description": "Ouvre une recherche YouTube dans le navigateur.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "send_email",
        "description": "Envoie un email via SMTP.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Prend un screenshot et le sauvegarde.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "default": "screenshot.png"}
            }
        }
    },
    {
        "name": "take_note",
        "description": "Prend une note et l'ajoute à notes.txt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {"type": "string"}
            },
            "required": ["note"]
        }
    },
    {
        "name": "external_sources",
        "description": "Accède aux sources externes ATHOS/Jarvis pour référence ou intégration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Recherche ou liste les repos"}
            }
        }
    }
]

# ── Exécuteurs d'outils ───────────────────────────────────────────────────────

def _log_tool(name: str, inputs: dict, result: str, record_kernel: bool = True):
    try:
        today   = datetime.now().strftime("%Y-%m-%d")
        log_dir = DRIVE / "logs"
        log_dir.mkdir(exist_ok=True)
        ts  = datetime.now().strftime("%H:%M:%S")
        inp = json.dumps(inputs, ensure_ascii=False)[:120].replace("\n", " ")
        res = result[:200].replace("\n", " ")
        with open(log_dir / f"{today}_tools.mem", "a") as f:
            f.write(f"§tool:{ts}|name:{name}|in:{inp}|out:{res}\n")
        if record_kernel:
            import session_kernel
            session_kernel.record_action(name, inp, res, engine="tool")
    except:
        pass

def tool_shell(command: str, timeout: int = 30) -> str:
    dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
    for d in dangerous:
        if d in command:
            return f"REFUSÉ : commande dangereuse ({d})"
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(Path.home())
        )
        out = (result.stdout + result.stderr).strip()
        return out[:3000] if out else "(exécuté, pas de sortie)"
    except subprocess.TimeoutExpired:
        return f"Timeout après {timeout}s"
    except Exception as e:
        return f"Erreur : {e}"

def tool_applescript(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=20
        )
        out = (result.stdout + result.stderr).strip()
        return out if out else "AppleScript exécuté"
    except Exception as e:
        return f"Erreur AppleScript : {e}"

def tool_open(target: str, app: str = "") -> str:
    if app:
        return tool_shell(f"open -a '{app}' '{target}'", 10)
    if target.startswith("http"):
        return tool_shell(f"open '{target}'", 10)
    return tool_shell(f"open '{target}' 2>/dev/null || open -a '{target}'", 10)

def tool_screenshot(prompt: str = "Décris ce que tu vois sur cet écran.", api_key: str = "") -> str:
    tmp = Path("/tmp/athos_screen.png")
    result = subprocess.run(["screencapture", "-x", str(tmp)], capture_output=True, timeout=5)
    if result.returncode != 0 or not tmp.exists():
        return "Impossible de prendre le screenshot"

    img_b64 = base64.standard_b64encode(tmp.read_bytes()).decode()

    if not api_key:
        env = Path(__file__).parent.parent / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()

    if not api_key:
        tmp.unlink(missing_ok=True)
        return f"Screenshot pris mais analyse impossible (pas de clé API). Fichier: {tmp}"

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 500,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=payload,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        tmp.unlink(missing_ok=True)
        return data["content"][0]["text"].strip()
    except Exception as e:
        tmp.unlink(missing_ok=True)
        return f"Erreur analyse screenshot : {e}"

def tool_calendar_read(days: int = 7) -> str:
    script = f'''
tell application "Calendar"
    set theDate to current date
    set endDate to theDate + ({days} * days)
    set output to ""
    repeat with cal in calendars
        set evts to (every event of cal whose start date >= theDate and start date <= endDate)
        repeat with evt in evts
            set evtDate to start date of evt
            set evtName to summary of evt
            set output to output & (evtDate as string) & " — " & evtName & return
        end repeat
    end repeat
    if output is "" then
        return "Aucun événement dans les {days} prochains jours."
    else
        return output
    end if
end tell'''
    result = tool_applescript(script)
    if "error" in result.lower() and "not running" not in result.lower():
        return f"Calendar.app inaccessible : {result}"
    return result

def tool_remind(message: str, minutes: int = 0, at_time: str = "") -> str:
    if at_time:
        time_part = at_time
        script = f'''
tell application "Reminders"
    make new reminder with properties {{name:"{message}", remind me date:date "{time_part}"}}
end tell'''
    elif minutes > 0:
        script = f'''
set theDate to (current date) + ({minutes} * minutes)
tell application "Reminders"
    make new reminder with properties {{name:"{message}", remind me date:theDate}}
end tell'''
    else:
        script = f'tell application "Reminders" to make new reminder with properties {{name:"{message}"}}'

    result = tool_applescript(script)
    if "error" in result.lower():
        # Fallback: notification différée
        if minutes > 0:
            delay_sec = minutes * 60
            tool_shell(
                f"(sleep {delay_sec} && osascript -e 'display notification \"{message}\" with title \"A.T.H.O.S.\" sound name \"Glass\"') &",
                5
            )
            return f"Rappel programmé dans {minutes} minute(s) : {message}"
        return f"Erreur Reminders : {result}"
    return f"Rappel créé : {message}"

def tool_network_scan(mode: str = "quick") -> str:
    results = []
    local_ip = tool_shell("ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null", 5).strip()
    subnet   = ".".join(local_ip.split(".")[:3]) if local_ip and "." in local_ip else "192.168.1"

    if mode in ("quick", "all"):
        arp = tool_shell("arp -a 2>/dev/null", 10)
        results.append(f"=== RÉSEAU ARP ===\n{arp}\nIP Mac : {local_ip}")

    if mode in ("deep", "all"):
        scan = tool_shell(f"nmap -sn {subnet}.0/24 --open -T4 2>/dev/null | grep -E 'report|MAC|Host'", 45)
        results.append(f"=== NMAP SCAN ===\n{scan}")

    if mode in ("bonjour", "all"):
        services = [
            ("AirPlay/Apple TV", "_airplay._tcp"),
            ("AirTunes/Sonos",   "_raop._tcp"),
            ("Chromecast",       "_googlecast._tcp"),
            ("HomeKit",          "_hap._tcp"),
            ("AirPrint",         "_ipp._tcp"),
            ("Spotify Connect",  "_spotify-connect._tcp"),
        ]
        found = []
        for name, svc in services:
            r = subprocess.run(["dns-sd", "-B", svc, "local"],
                               capture_output=True, text=True, timeout=4)
            lines = [l for l in r.stdout.splitlines() if "." in l and "BROWSE" not in l]
            if lines:
                found.append(f"{name}: {lines[-1].strip()}")
        results.append("=== SERVICES BONJOUR ===\n" + ("\n".join(found) if found else "Aucun"))

    if mode in ("bluetooth", "all"):
        bt = tool_shell(
            "blueutil --paired --format json 2>/dev/null | "
            "python3 -c \"import sys,json;[print(d.get('name','?'),d.get('connected','?')) "
            "for d in json.load(sys.stdin)]\"", 10
        )
        results.append(f"=== BLUETOOTH PAIRED ===\n{bt}")

    if mode in ("wifi", "all"):
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        wifi = tool_shell(f"{airport} -I 2>/dev/null", 10)
        results.append(f"=== WIFI ===\n{wifi}")

    if mode in ("security", "all"):
        ports = tool_shell("lsof -i -nP | grep LISTEN | awk '{print $1,$9}' | sort -u", 10)
        fw    = tool_shell("defaults read /Library/Preferences/com.apple.alf globalstate 2>/dev/null", 5)
        results.append(f"=== SÉCURITÉ ===\nFirewall: {fw.strip()}\n{ports}")

    return "\n\n".join(results) if results else "Aucun résultat"

def tool_http_request(url: str, method: str = "GET", body: str = "", headers: dict = None) -> str:
    try:
        data = body.encode() if body else None
        req  = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()[:2000]
    except Exception as e:
        return f"Erreur HTTP : {e}"

def tool_write_file(path: str, content: str, mode: str = "write") -> str:
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        if mode == "append":
            with open(p, "a") as f: f.write(content)
        else:
            p.write_text(content)
        return f"Fichier écrit : {path} ({len(content)} chars)"
    except Exception as e:
        return f"Erreur écriture : {e}"

def tool_memory_write(file: str, content: str) -> str:
    try:
        target = DRIVE / file
        with open(target, "a", encoding="utf-8") as f:
            f.write(f"\n{content}\n")
        return f"Mémorisé dans {file}"
    except Exception as e:
        return f"Erreur mémoire : {e}"

def tool_memory_read(file: str) -> str:
    try:
        target = DRIVE / file
        if not target.exists():
            return f"{file} introuvable"
        return target.read_text("utf-8")[:2500]
    except Exception as e:
        return f"Erreur lecture : {e}"

def tool_notify(title: str, message: str, sound: str = "Glass") -> str:
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
    subprocess.Popen(["osascript", "-e", script])
    return f"Notification : {title}"

def tool_system_info(query: str) -> str:
    parts = []
    q = query.lower()
    if q in ("battery", "all"):
        parts.append(f"Batterie:\n{tool_shell('pmset -g batt 2>/dev/null | head -2', 5)}")
    if q in ("cpu", "all"):
        parts.append(f"CPU:\n{tool_shell('top -l1 -n0 | grep CPU', 5)}")
    if q in ("ram", "all"):
        parts.append(f"RAM:\n{tool_shell('top -l1 -n0 | grep PhysMem', 5)}")
    if q in ("disk", "all"):
        parts.append(f"Disque:\n{tool_shell('df -h / | tail -1', 5)}")
    if q in ("processes", "all"):
        parts.append("CPU top:\n" + tool_shell('ps aux | sort -rk3 | head -8 | awk \'{print $3"%", $11}\'', 5))
    if q in ("apps", "all"):
        parts.append("Apps:\n" + tool_shell("osascript -e 'tell app \"System Events\" to get name of every process whose background only is false'", 5))
    if q in ("time", "all"):
        parts.append("Date/heure:\n" + tool_shell("date '+%A %d %B %Y, %H:%M:%S'", 5))
    if q == "all":
        parts.append("IP: " + tool_shell('ipconfig getifaddr en0 2>/dev/null', 5).strip())
    return "\n\n".join(parts) if parts else "Query '" + query + "' non reconnue. Options: battery, cpu, ram, disk, processes, apps, time, all"

def tool_clipboard(action: str, content: str = "") -> str:
    if action == "read":
        return tool_shell("pbpaste", 5)
    elif action == "write":
        subprocess.run("pbcopy", input=content.encode(), timeout=5)
        return f"Presse-papier mis à jour ({len(content)} chars)"
    return "Action inconnue (read ou write)"

def tool_media_control(action: str, target: str = "") -> str:
    if action == "list_outputs":
        return tool_shell(
            "SwitchAudioSource -a -t output 2>/dev/null || "
            "system_profiler SPAudioDataType 2>/dev/null | grep -A2 'Output' | head -20", 10
        )
    if action == "airplay_to" and target:
        script = f'''tell application "Music"
    set AirPlay devices to (get AirPlay devices whose name contains "{target}")
end tell'''
        return tool_applescript(script)
    if action in ("play", "pause", "next", "prev"):
        cmds = {"play": "play", "pause": "pause", "next": "next track", "prev": "previous track"}
        r = tool_applescript(f'tell application "Music" to {cmds[action]}')
        if "error" in r.lower():
            r = tool_applescript(f'tell application "Spotify" to {cmds[action]}')
        return r
    if action in ("volume_up", "volume_down", "set_volume", "mute"):
        if action == "set_volume" and target:
            script = f'set volume output volume {target}'
        elif action == "volume_up":
            script = 'set volume output volume ((output volume of (get volume settings)) + 10)'
        elif action == "volume_down":
            script = 'set volume output volume ((output volume of (get volume settings)) - 10)'
        else:
            script = 'set volume with output muted'
        return tool_applescript(script)
    return f"Action '{action}' non reconnue"

def tool_wikipedia(query: str, sentences: int = 2) -> str:
    from tools.wikipedia import search_wikipedia
    return search_wikipedia(query, sentences)

def tool_youtube(query: str) -> str:
    from tools.youtube import search_youtube
    return search_youtube(query)

def tool_send_email(to: str, subject: str, body: str) -> str:
    from tools.email_tool import send_email
    return send_email(to, subject, body)

def tool_take_screenshot(filename: str = "screenshot.png") -> str:
    from tools.screenshot import take_screenshot
    return take_screenshot(filename)

def tool_take_note(note: str) -> str:
    from tools.note import take_note
    return take_note(note)

def tool_external_sources(query: str = "") -> str:
    sources = [
        {
            "name": "codewithbro95/J.A.R.V.I.S",
            "use": "Ollama local, vision webcam/LLaVA, wrapper d'outils, patterns Kokoro/LuxTTS",
            "files": "main.py, modules/ollama_nlp.py, modules/vibranium/vision/vision.py",
        },
        {
            "name": "GauravSingh9356/J.A.R.V.I.S",
            "use": "commandes desktop, Wikipedia, YouTube, email, screenshot, notes, weather, OCR",
            "files": "jarvis.py, helpers.py, youtube.py, news.py, OCR.py",
        },
        {
            "name": "kishanrajput23/Jarvis-Desktop-Voice-Assistant",
            "use": "boucle voix/TTS simple, commandes assistant desktop de base",
            "files": "Jarvis/jarvis.py",
        },
        {
            "name": "201Harsh/IRIS-AI",
            "use": "architecture agent OS, tool registry, terminal overlay, IPC, workflows, RAG",
            "files": "README.md, Agents.md, src/main/logic/*, src/main/services/*",
        },
    ]
    q = (query or "").lower()
    if q:
        sources = [s for s in sources if q in s["name"].lower() or q in s["use"].lower() or q in s["files"].lower()]
    if not sources:
        return "Aucune source externe ATHOS ne correspond à cette recherche."
    return "\n".join(f"- {s['name']} | use:{s['use']} | files:{s['files']}" for s in sources)

# ── Dispatch ──────────────────────────────────────────────────────────────────

_API_KEY_CACHE = {"key": ""}

def _get_api_key() -> str:
    if _API_KEY_CACHE["key"]:
        return _API_KEY_CACHE["key"]
    env = Path(__file__).parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                _API_KEY_CACHE["key"] = line.split("=", 1)[1].strip()
    return _API_KEY_CACHE["key"]

def execute_tool(name: str, inputs: dict, record_kernel: bool = True) -> str:
    def _web_search():
        from web import search_web, search_news, search_arxiv, search_wikipedia, format_search_results
        src = inputs.get("source", "web")
        q   = inputs["query"]
        n   = inputs.get("max_results", 5)
        if src == "arxiv":      return format_search_results(search_arxiv(q, n), "arxiv")
        elif src == "news":     return format_search_results(search_news(q, n), "news")
        elif src == "wikipedia":
            r = search_wikipedia(q)
            return f"{r['title']}\n{r['summary']}\n{r['url']}"
        return format_search_results(search_web(q, n), "web")

    dispatch = {
        "shell":          lambda: tool_shell(inputs["command"], inputs.get("timeout", 30)),
        "applescript":    lambda: tool_applescript(inputs["script"]),
        "open":           lambda: tool_open(inputs["target"], inputs.get("app", "")),
        "screenshot":     lambda: tool_screenshot(inputs.get("prompt", "Décris ce que tu vois."), _get_api_key()),
        "calendar_read":  lambda: tool_calendar_read(inputs.get("days", 7)),
        "remind":         lambda: tool_remind(inputs["message"], inputs.get("minutes", 0), inputs.get("at_time", "")),
        "network_scan":   lambda: tool_network_scan(inputs.get("mode", "quick")),
        "http_request":   lambda: tool_http_request(inputs["url"], inputs.get("method", "GET"), inputs.get("body", ""), inputs.get("headers", {})),
        "write_file":     lambda: tool_write_file(inputs["path"], inputs["content"], inputs.get("mode", "write")),
        "memory_write":   lambda: tool_memory_write(inputs["file"], inputs["content"]),
        "memory_read":    lambda: tool_memory_read(inputs["file"]),
        "notify":         lambda: tool_notify(inputs["title"], inputs["message"], inputs.get("sound", "Glass")),
        "system_info":    lambda: tool_system_info(inputs["query"]),
        "clipboard":      lambda: tool_clipboard(inputs["action"], inputs.get("content", "")),
        "media_control":  lambda: tool_media_control(inputs["action"], inputs.get("target", "")),
        "web_search":     _web_search,
        "fetch_url":      lambda: __import__("web").fetch_page(inputs["url"]),
        "install_skill":  lambda: _install_skill(),
        "list_skills":    lambda: __import__("skill_manager").capabilities_report(),
        "wikipedia":      lambda: tool_wikipedia(inputs["query"], inputs.get("sentences", 2)),
        "youtube":        lambda: tool_youtube(inputs["query"]),
        "send_email":     lambda: tool_send_email(inputs["to"], inputs["subject"], inputs["body"]),
        "take_screenshot": lambda: tool_take_screenshot(inputs.get("filename", "screenshot.png")),
        "take_note":      lambda: tool_take_note(inputs["note"]),
        "external_sources": lambda: tool_external_sources(inputs.get("query", "")),
    }

    def _install_skill():
        from skill_manager import install_skill
        ok, msg = install_skill(inputs["skill_name"], _get_api_key())
        return msg

    fn = dispatch.get(name)
    if not fn:
        return f"Outil inconnu : {name}"
    result = fn()
    _log_tool(name, inputs, result, record_kernel=record_kernel)
    return result

# ── ReAct Loop ────────────────────────────────────────────────────────────────

_AUTHORIZE_WORDS = {
    "lance", "go", "oui", "fais-le", "exécute", "execute",
    "confirme", "ok", "vas-y", "yes", "do it", "allons-y",
    "démarre", "commence", "fais", "fait"
}

def _is_authorized(msg: str) -> bool:
    normalized = msg.lower().replace("'", " ").replace("-", " ").strip()
    words = set(normalized.split())
    direct_authorizations = _AUTHORIZE_WORDS | {"vas y", "allons y", "fais le"}
    if normalized in direct_authorizations:
        return True
    explicit_phrases = {
        "lance le plan", "lance ça", "lance ca", "vas y lance", "ok lance",
        "oui execute", "oui exécute", "fais le", "fais-le maintenant",
        "go execute", "go exécute", "confirme execution", "confirme exécution"
    }
    if any(phrase in normalized for phrase in explicit_phrases):
        return True
    return bool(words & {"lance", "exécute", "execute"})

def run_agent(msg: str, system: str, history: list, api_key: str,
              on_action=None) -> str:
    """
    Boucle ReAct avec confirmation obligatoire.
    Sans autorisation → plan texte (tool_choice: none)
    Avec autorisation → exécution complète (tool_choice: auto)
    """
    authorized  = _is_authorized(msg)
    tool_choice = {"type": "auto"} if authorized else {"type": "none"}
    messages    = history + [{"role": "user", "content": msg}]

    for _ in range(MAX_ITERATIONS):
        payload = json.dumps({
            "model":       "claude-sonnet-4-6",
            "max_tokens":  2048,
            "system":      system,
            "tools":       TOOLS,
            "tool_choice": tool_choice,
            "messages":    messages
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                response = json.loads(r.read())
        except Exception as e:
            raise   # propagé vers server.py pour gestion engine fallback

        stop_reason = response.get("stop_reason")
        content     = response.get("content", [])

        if stop_reason == "end_turn":
            return " ".join(b["text"] for b in content if b.get("type") == "text").strip()

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": content})
            tool_results = []
            for block in content:
                if block.get("type") != "tool_use":
                    continue
                t_name   = block["name"]
                t_inputs = block["input"]
                t_id     = block["id"]
                result   = execute_tool(t_name, t_inputs, record_kernel=on_action is None)
                if on_action:
                    on_action(t_name, t_inputs, result)
                tool_results.append({
                    "type": "tool_result", "tool_use_id": t_id, "content": result
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        # Réponse inattendue — extraire le texte quand même
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        if texts:
            return " ".join(texts).strip()
        break

    return "Terminé."
