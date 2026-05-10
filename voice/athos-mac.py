"""ATHOS — Interface vocale Mac | sox + Claude API + say"""
import os, sys, json, subprocess, urllib.request, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
import config

API_KEY = config.ANTHROPIC_KEY
DRIVE = config.DRIVE

SYSTEM = """Tu es A.T.H.O.S. — Autonomous Tactical Heuristic Operating System.
IA personnelle de Clément, fondateur d'Ex-Nihilo Agency.
Ton : majordome. Direct, posé, précis. Humour sec si pertinent.
Jamais servile. Toujours français. Réponses courtes pour la voix (2-3 phrases max)."""

def say(text: str):
    """TTS macOS — voix Thomas (FR)"""
    subprocess.run(["say", "-v", "Thomas", "-r", "175", text])

def record() -> str:
    """Enregistre depuis le micro jusqu'au silence"""
    tmp = tempfile.mktemp(suffix=".wav")
    print("  [ATHOS] Écoute... (Ctrl+C pour annuler)")
    subprocess.run([
        "sox", "-d", "-r", "16000", "-c", "1", tmp,
        "silence", "1", "0.3", "1%", "1", "1.5", "1%"
    ], stderr=subprocess.DEVNULL)
    return tmp

def transcribe(wav_path: str) -> str:
    """STT via OpenAI Whisper API"""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        # Fallback : speech_recognition Google (gratuit)
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = r.record(source)
            return r.recognize_google(audio, language="fr-FR")
        except Exception as e:
            return ""

    with open(wav_path, "rb") as f:
        boundary = "----FormBoundary"
        body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
        body += f.read()
        body += f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-1\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()).get("text", "")
    except:
        return ""

def ask_athos(text: str) -> str:
    ctx = []
    for f in ["athos_identity.mem", "athos_projects.mem"]:
        p = DRIVE / f
        if p.exists():
            ctx.append(p.read_text("utf-8")[:600])

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 250,
        "system": SYSTEM + "\n\nCONTEXTE:\n" + "\n".join(ctx),
        "messages": [{"role": "user", "content": text}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception as e:
        return f"Erreur : {e}"

def main():
    # Vérifier sox
    if subprocess.run(["which", "sox"], capture_output=True).returncode != 0:
        print("§error:sox_manquant — brew install sox")
        sys.exit(1)

    say("Système en ligne.")
    print("§athos:mac_voice|status:ready")
    print("§usage: Parle après le signal. Ctrl+C pour quitter.\n")

    while True:
        try:
            input("  [Entrée pour parler] ")
            wav = record()
            print("  [ATHOS] Analyse...")
            text = transcribe(wav)
            Path(wav).unlink(missing_ok=True)

            if not text.strip():
                say("Je n'ai pas compris.")
                continue

            print(f"  [Toi] {text}")
            reply = ask_athos(text)
            print(f"  [ATHOS] {reply}\n")
            say(reply)

        except KeyboardInterrupt:
            print("\n§athos:mac_voice|status:shutdown")
            say("À bientôt.")
            break

if __name__ == "__main__":
    main()
