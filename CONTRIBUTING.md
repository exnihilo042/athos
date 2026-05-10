# Guide de contribution - Athos

## 🔐 Sécurité et bonnes pratiques

### Gestion des secrets
- **NE JAMAIS** commiter de clés API ou mots de passe
- Utiliser uniquement des variables d'environnement
- Le fichier `.env` est exclu de Git - créer un `.env.example` avec des placeholders

### Code review
- Toutes les PR nécessitent une review
- Tester les changements avant soumission
- Respecter la structure existante du projet

## 🛠️ Configuration de développement

### Environnement local
```bash
# Après avoir cloné le repo
./install.sh
cp .env.example .env
# Éditer .env avec vos propres clés API
```

### Structure du projet
```
athos/
├── core/           # Logique métier Python
├── voice/          # Interface web et serveur
├── routines/       # Automatisations (launchd)
├── temp/           # Sessions temporaires
├── logs/           # Logs d'exécution
└── config/         # Configuration système
```

## 📋 Checklist avant contribution

- [ ] Code testé localement
- [ ] Pas de secrets dans les commits
- [ ] Documentation mise à jour si nécessaire
- [ ] Changements compatibles avec l'architecture existante
- [ ] Variables d'environnement utilisées pour les configs sensibles

## 🚀 Déploiement

### Pour les contributeurs
1. Fork le repo
2. Créer une branche feature
3. Commiter et pousser
4. Ouvrir une PR avec description détaillée

### Pour les mainteneurs
1. Review du code
2. Tests automatisés si présents
3. Merge après validation

## 🐛 Signaler un bug

Utiliser les Issues GitHub avec :
- Description claire du problème
- Étapes pour reproduire
- Logs pertinents (sans secrets)
- Environnement (OS, Python version)

## 💡 Proposer une fonctionnalité

Créer une Issue avec :
- Description de la fonctionnalité
- Cas d'usage
- Impact sur l'architecture existante
- Éventuels breaking changes