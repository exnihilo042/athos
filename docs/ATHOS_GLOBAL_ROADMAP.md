# Plan Global ATHOS — JARVIS Local-First

## P0 — Viabilité

- Attachement obligatoire IA: `/api/attach`, `/api/context_pack`, `/api/delegate`, `/api/report`, `/api/checkpoint`.
- Prompt kit copiable dans Codex, Claude, Grok ou autre moteur.
- Prompt texte fiable depuis Athos.
- Vocal STT réel validé sans Whisper payant par défaut.
- OBS lisible: process, ports, launchd, logs, moteurs attachés, sync, devices, skills, coûts.
- Zéro dépense API par défaut.
- Plan/lance visible pour toute mutation.
- Boucle autonome en mode guarded: start explicite, statut observable, events JSONL, mutation de skill bloquée par défaut.
- Capacité locale austère: sans réseau, sans capteurs et sans nouveau moteur, Athos scanne les ressources disponibles, compresse le contexte, raisonne depuis mémoire locale, simule, agit réversiblement et queue les actions réseau.
- Garde-fou vérité: vérité/calibration/correction des biais avant confort, flatterie ou validation de croyances faibles.
- Graphe de capacités: moteurs, mémoire, outils locaux, skills, protocoles, appareils, hardware, sync et garde-fous sont des nœuds reliés, pas des listes fixes par tâche.
- Sources externes intégrées: Hermes → profils moteurs/SSE; gbrain → ledger vérité/provenance; gstack → pipeline de revue situationnel.

## P1 — Ce Mois

- Routing situationnel: simple local, code lourd via ChatGPT Plus/Claude Code, API seulement si explicitement autorisée, Ollama en dernier secours.
- Routing par graphe: réutiliser les capacités existantes et leurs relations avant d'ajouter une règle spéciale.
- HUD command center: noyau central, agents actifs, metriques projet, actions en cours, blocages, health runtime et Room compacte.
- Crew ATHOS: sous-agents roles visibles (Operator, Dev, Growth, Support, Analyst, Archivist) sous identite unique ATHOS.
- Project telemetry registry: projets suivis avec sources, metriques, seuils, risques, routines et prochaine action.
- Protocoles metier executables: `ATHOS_GROWTH_REVIEW`, `ATHOS_CLIENT_DAILY`, `ATHOS_CREATIVE_PIPELINE`, `ATHOS_DEV_HANDOFF`, `ATHOS_SUPPORT_TRIAGE`.
- Sync manager Drive/GitHub/serveur privé avec outbox offline.
- Mémoire long terme opérable: résumé session, checkpoint, récupération crash, nettoyage conflits.
- Voix meilleure: moteur local gratuit si possible, service externe seulement opt-in.
- Gmail/Calendar après permission.
- Widgets contextuels générés par tâche.

## P2 — Système Distribué

- Skill Registry robuste: permissions, dépendances, tests, offline status, compatibilité appareil (voir `docs/SKILL_REGISTRY_SPEC.md` — catalogue P3 fondé sur la base v8 actuelle).
- Edge agents autorisés: Mac, téléphone, serveur privé, TV si scope explicite.
- Token, permissions, heartbeat, logs, queue offline par appareil.
- PWA mobile stable + accès sécurisé distant.
- Skill registry robuste: permissions, dépendances, tests, offline status, compatibilité appareil.
- Capability graph persistant: score d'interconnexion, dépendances, risques, coûts, offline readiness, tests associés.
- Connecteurs moteurs supplémentaires depuis le registre Hermes/Athos: OpenRouter, Google, Qwen, MiniMax, LM Studio, vLLM, llama.cpp, Groq, DeepSeek, Together, Fireworks, Cerebras, Mistral. Tous restent soumis à la politique coût/scopes.

## P3 — JARVIS Avancé

- Vision écran/webcam avec consentement.
- Wake word.
- Contrôle Mac avancé.
- Scan réseau défensif uniquement sur réseaux autorisés.
- Hardware layer: LiDAR, Flipper Zero, outils Wi-Fi, caméras, capteurs.

## P4 — Long Terme

- VPS always-on.
- HUD AR / lunettes.
- Routines nommées avancées.
- Robotique et multi-environnements.

## Protocoles Nommés

- `ATHOS_STATUS`: état système complet.
- `ATHOS_SECURE_DEVICE`: sécuriser un appareil autorisé.
- `ATHOS_SCAN_NETWORK`: scan défensif réseau autorisé.
- `ATHOS_SELF_IMPROVE`: détecter gap, chercher, proposer, installer, tester, commit/push, mémoriser.
- `ATHOS_SYNC`: synchroniser mémoire et jobs différés.
- `ATHOS_CLEAN_ROOM`: rendre l'environnement lisible et minimal.

## Patterns JARVIS Transposés

- Interface naturelle + opérateur système.
- Contexte permanent.
- Télémétrie concise.
- Proactivité contrôlée.
- Protocoles nommés.
- Arrière-plan visible et stoppable.
- Garde-fous forts contre l'effet Ultron/E.D.I.T.H.
- Physical world bridge = amplificateur, pas prérequis: Athos doit rester capable en austérité locale.
- Épistémologie anti-complaisance: Athos doit casser les illusions utiles à court terme mais toxiques pour la décision.

Sources de référence produit:

- videos locales `jarvis 1.mp4` a `jarvis 4.mp4` dans Downloads; analyse: `docs/JARVIS_VIDEO_ANALYSIS_2026-05-20.md`
- https://www.marvel.com/characters/iron-man-tony-stark/on-screen
- https://www.marvel.com/articles/games/marvels-iron-man-vr-tony-stark-top-tech
- https://marvelcinematicuniverse.fandom.com/wiki/J.A.R.V.I.S.
- https://marvelcinematicuniverse.fandom.com/wiki/J.A.R.V.I.S./Quote
- https://movies.fandom.com/wiki/Iron_Man_2/Transcript
- https://marvelcinematicuniverse.fandom.com/wiki/E.D.I.T.H.
