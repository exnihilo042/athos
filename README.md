# Athos - AI Assistant

Athos est un assistant IA vocal avec interface web, utilisant Claude (Anthropic) et Ollama comme moteurs de conversation.

## 🚀 Démarrage rapide

### Prérequis
- Python 3.14+
- Ollama (pour le mode dégradé)
- Cloudflare Tunnel (cloudflared)

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

3. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env et ajouter votre ANTHROPIC_API_KEY
   ```

4. **Lancer l'application**
   ```bash
   ./voice/start.sh
   ```

L'application sera accessible via un tunnel Cloudflare temporaire.

## 🏗️ Architecture

- `core/` - Logique métier et gestion mémoire
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

## 📄 Licence

Ce projet est sous licence propriétaire - voir les termes d'utilisation d'Ex Nihilo Agency.