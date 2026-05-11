# A.T.H.O.S. - Autonomous Tactical Heuristic Operating System

Athos est une couche cognitive et runtime multi-moteur. ChatGPT Plus CLI, Claude Code Pro, APIs autorisées, Grok et Ollama sont des moteurs remplaçables; l'identité, la mémoire, l'observabilité, les permissions, le graphe de capacités et les checkpoints appartiennent à Athos.

Objectif produit: transformer un LLM en organe d'un système opérant, local-first, observable, capable de fonctionner en austérité locale et de compenser les limites de contexte, scope, coût ou rigidité des moteurs.

## 📁 Structure du projet

```
athos/
├── core/           # Logique métier et gestion mémoire Python
├── voice/          # Interface web PWA et serveur HTTP
├── routines/       # Automatisations (briefs quotidiens/hebdomadaires)
├── memory/         # Fichiers mémoire Athos (contexte et apprentissage)
├── docs/           # Documentation système
├── temp/           # Sessions temporaires
├── logs/           # Logs d'exécution
└── tests/          # Suite de tests pytest
```

## 🧠 Fichiers mémoire essentiels

Le cerveau d'Athos est composé de fichiers `.mem` contenant son contexte et apprentissage :

- **`memory/athos_identity.mem`** - Identité, persona et règles de base
- **`memory/athos_capabilities.mem`** - Capacités complètes du système
- **`memory/athos_projects.mem`** - Suivi des projets actifs
- **`memory/cx_global.mem`** - Préférences utilisateur générales
- **`memory/athos_session_kernel.jsonl`** - Session courante indépendante du moteur, utilisée pour reprendre le contexte après failover
- **`ATHOS_ATTACH_PROMPT.md`** - Boot universel Athos pour tout moteur
- **`ATHOS_ATTACH_PROTOCOL.md`** - Contrat d'attachement inter-moteur
- **`docs/CLAUDE.md`** - Documentation système et contexte agence historique

Ces fichiers sont automatiquement chargés à chaque démarrage pour maintenir la cohérence d'Athos.

## 🚀 Démarrage rapide

### Prérequis
- Python 3.14+
- Ollama (pour le mode dégradé)
- Cloudflare Tunnel (cloudflared) uniquement si exposition distante temporaire souhaitée

### Installation

1. **Cloner le repo**
   ```bash
   git clone https://github.com/exnihilo042/athos.git
   cd athos
   ```

2. **Installer les dépendances**
   ```bash
   ./install.sh
   ```
   Le fallback vocal serveur nécessite aussi `ffmpeg` (`brew install ffmpeg` sur macOS).

3. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env si besoin.
   # Vous pouvez aussi définir DRIVE_PATH pour stocker la mémoire en dehors du repo.
   # Pour exposer Athos en ligne, définir ATHOS_ACCESS_TOKEN et le saisir dans les réglages de l'interface.
   # Ordre moteur par défaut : ATHOS_ENGINE_ORDER=chatgpt_plus,claude_code,anthropic_api,grok,ollama
   # Modèle OpenAI configurable : OPENAI_MODEL=gpt-4.1
   # Sécurité coût : ATHOS_API_SPEND=off interdit les APIs payantes par défaut.
   # OPENAI_ENABLED=false garde la clé stockée mais interdit les appels OpenAI.
   # WHISPER_ENABLED=false garde la transcription sur fallback gratuit.
   # ATHOS_SKILL_INSTALL_ENABLED=false transforme l'auto-extension en plan visible.
   ```

4. **Lancer l'application**
   ```bash
   ./voice/start.sh
   ```

5. **Tester**
   ```bash
   python3 -m pytest
   ```

Par défaut, le serveur écoute en local sur `127.0.0.1:7474`. L'exposition distante doit rester protégée par `ATHOS_ACCESS_TOKEN`.

## 🏗️ Architecture

- `core/` - Logique métier et gestion mémoire
- `core/operating_protocol.py` - Protocole de travail noyau injecté dans tous les moteurs
- `core/reasoning_kernel.py` - Journal d'action visible et routage mental Athos
- `core/observability.py` - Ports, processus, launchd, logs, Git et mémoire visibles
- `core/capability_graph.py` - Graphe interconnecté des moteurs, outils, skills, appareils, mémoire et garde-fous
- `core/local_capability.py` - Capacité locale austère sans réseau ni capteurs obligatoires
- `core/epistemic_guard.py` - Vérité, calibration et correction des biais avant confort utilisateur
- `voice/` - Interface web et serveur HTTP
- `routines/` - Tâches automatisées (briefs quotidiens/hebdomadaires)
- `temp/` - Fichiers temporaires de session

## 🤝 Contribution

### Pour contribuer :

1. Fork le repo
2. Créer une branche feature : `git checkout -b feature/nouvelle-fonction`
3. Commiter vos changements : `git commit -m 'Ajout nouvelle fonctionnalité'`
4. Push vers la branche : `git push origin feature/nouvelle-fonction`
5. Ouvrir une Pull Request

### Configuration de développement

- Ne jamais commiter de clés API (fichier `.env`)
- Utiliser des variables d'environnement pour les secrets
- Tester avec `python3 -m pytest` si des tests sont ajoutés

## 📝 Notes importantes

- Le fichier `.env` contient des clés API sensibles - il est exclu de Git
- Les logs sont stockés dans `logs/` et `temp/`
- Le budget API est tracké dans `budget.json`

## 🔧 Scripts disponibles

- `./install.sh` - Installation complète
- `./voice/start.sh` - Démarrage avec tunnel Cloudflare
- `./note` - Ajout rapide de notes en session
- `./routines/run_brief.sh` - Génération du brief quotidien
- `./routines/run_weekly.sh` - Consolidation hebdomadaire
- Aucune CI GitHub Actions n'est actuellement présente dans le repo; les tests sont lancés localement avant chaque push.

## 🔊 Voix

Athos utilise d'abord les voix système gratuites du navigateur ou de macOS. Sur Mac récent, l'interface privilégie automatiquement une voix française moderne (`Reed`, `Eddy`, `Rocko`) avant l'ancien fallback `Thomas`.

## ✅ Règle de livraison Athos

Toute modification d'Athos doit suivre ce cycle :

1. Implémenter une tranche courte et vérifiable.
2. Lancer les tests métier et techniques (`pytest`, compilation Python, contrôle API local si serveur touché).
3. Mettre à jour la mémoire Drive utile.
4. Commiter proprement et pousser sur GitHub.

## 📄 Licence

Ce projet est sous licence propriétaire - voir les termes d'utilisation d'Ex Nihilo Agency.
