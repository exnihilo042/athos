#!/bin/bash
# ATHOS — Lance serveur vocal + Cloudflare Tunnel

ATHOS=~/Sites/athos
source "$ATHOS/.env" 2>/dev/null

clear
echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║      A.T.H.O.S. — VOICE          ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# 1. Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  [1/3] Démarrage Ollama..."
    ollama serve > /tmp/athos_ollama.log 2>&1 &
    sleep 3
else
    echo "  [1/3] Ollama : déjà actif"
fi

# 2. Serveur ATHOS
lsof -ti:7474 | xargs kill -9 2>/dev/null
sleep 1
echo "  [2/3] Serveur ATHOS sur :7474..."
"$ATHOS/venv/bin/python3" "$ATHOS/voice/server.py" >> /tmp/athos_server.log 2>&1 &
SERVER_PID=$!
sleep 2

# Vérifier que le serveur répond
if curl -s http://localhost:7474/api/status -X POST > /dev/null 2>&1; then
    echo "  [2/3] Serveur OK (PID $SERVER_PID)"
else
    echo "  [2/3] ERREUR — serveur ne répond pas"
    echo "        Log : tail -f /tmp/athos_server.log"
    exit 1
fi

# 3. Cloudflare Tunnel
echo "  [3/3] Tunnel Cloudflare..."
echo ""

cloudflared tunnel --url http://localhost:7474 2>&1 | while IFS= read -r line; do
    URL=$(echo "$line" | grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' | head -1)
    if [ -n "$URL" ]; then
        # Attendre que l'URL soit réellement joignable
        echo "  Tunnel établi, vérification connexion..."
        for i in 1 2 3 4 5; do
            if curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null | grep -q "200"; then
                break
            fi
            sleep 2
        done
        clear
        echo ""
        echo "  ╔══════════════════════════════════════════╗"
        echo "  ║         A.T.H.O.S. — EN LIGNE            ║"
        echo "  ╚══════════════════════════════════════════╝"
        echo ""
        echo "  Moteur  : $(curl -s -X POST http://localhost:7474/api/status | python3 -c 'import sys,json; print(json.load(sys.stdin)["engine"].upper())' 2>/dev/null || echo 'OLLAMA')"
        echo ""
        echo "  ┌──────────────────────────────────────────┐"
        echo "  │  $URL"
        echo "  └──────────────────────────────────────────┘"
        echo ""
        echo "  iPhone : Safari → URL ci-dessus"
        echo "           Partager → Sur l'écran d'accueil"
        echo ""
        echo "  Log serveur : tail -f /tmp/athos_server.log"
        echo ""
        echo "$URL" | pbcopy
        echo "  (URL copiée · Ctrl+C pour arrêter)"
        echo ""
        open -a Safari "$URL" 2>/dev/null
    fi
done
