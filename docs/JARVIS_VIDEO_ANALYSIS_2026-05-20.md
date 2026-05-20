# Analyse Source Produit — Videos JARVIS 1-4

Source locale analysee:

- `/Users/clem/Downloads/jarvis 1.mp4`
- `/Users/clem/Downloads/jarvis 2.mp4`
- `/Users/clem/Downloads/jarvis 3.mp4`
- `/Users/clem/Downloads/jarvis 4.mp4`

Artefacts d'analyse:

- frames: `temp/jarvis_video_analysis/frames/`
- keyframes: `temp/jarvis_video_analysis/keyframes/`
- audio: `temp/jarvis_video_analysis/audio/`
- tentative STT offline: `temp/jarvis_video_analysis/transcripts_base/`

## Limites De Lecture

- Les videos sont des captures verticales d'un setup physique multi-ecrans, pas un export direct de l'application.
- La transcription audio offline `whisper.cpp` avec `tiny.en` puis `base.en` est inutilisable: audio trop degrade/bruite ou voix trop masquee par la captation. Ne pas en tirer de verbatim fiable.
- Les informations exploitables viennent surtout des sous-titres incrustes et de l'interface visible.

## Synthese

Le systeme montre un "JARVIS business operator", pas un simple chatbot.

Le coeur produit:

- une interface plein ecran type command center;
- un noyau orbital central qui signale l'etat actif du systeme;
- des panneaux de telemetrie permanents;
- des agents/personas nommes;
- des protocoles activables par phrase;
- des actions multi-outils: analytics, ads, Slack, Drive, PR, bugfix, decisions budgetaires;
- une reponse vocale concise, proactive et orientee business.

## Patterns Observes

### 1. Command Center Permanent

L'interface principale reste visuellement stable pendant les actions:

- grand noyau central anime;
- panneaux gauche/droite fixes;
- horloge et coordonnees systeme;
- boutons de modes en haut;
- widgets de signal, radar, waveform, log.

Implication ATHOS:

- le panneau Room ne suffit pas;
- il faut un mode HUD principal stable ou la voix, les agents, les stats, les actions et les logs coexistent;
- le centre doit afficher "ce qu'Athos fait maintenant", pas seulement une conversation.

### 2. Business Telemetry First

Les videos parlent en metriques:

- MRR;
- downloads;
- revenue;
- ad spend;
- ROAS;
- total views;
- best performer;
- content output;
- tickets/refunds;
- PR/backend status.

Implication ATHOS:

- chaque projet doit avoir un dashboard metier branche a ses sources;
- Athos doit etre capable de repondre "comment va X ?" par etat + metriques + recommandation;
- les projets clients doivent devenir des objets suivis, pas seulement des dossiers.

### 3. Agents Nommés Et Roles

Exemples observes via sous-titres:

- Sarah: support / knowledge / bug routing;
- Luke: footage / raw assets / creative input;
- Bobby: ads / scaling winners / cutting losers;
- Tom: developer agent / backend PR / tests.

Implication ATHOS:

- conserver l'identite unique ATHOS, mais ajouter des sous-agents roles;
- chaque role doit avoir scopes, sources, droits, sorties attendues;
- la Room actuelle Claude/Codex doit evoluer vers une "crew" visible: role, moteur, etat, derniere action.

### 4. Protocoles Nommés

Exemple observe:

- "Initiate Avengers protocol"

Le protocole declenche une sequence multi-agent:

- presenter l'equipe;
- router une demande;
- collecter donnees;
- escalader Slack si besoin;
- ouvrir PR/code;
- tirer assets depuis Drive;
- prendre decisions ads/content.

Implication ATHOS:

- les protocoles nommes doivent devenir des workflows executables;
- `ATHOS_SELF_IMPROVE`, `ATHOS_STATUS`, etc. doivent avoir phases, acteurs, conditions d'arret et recap;
- ajouter des protocoles metier: `ATHOS_GROWTH_REVIEW`, `ATHOS_CLIENT_DAILY`, `ATHOS_CREATIVE_PIPELINE`, `ATHOS_DEV_HANDOFF`.

### 5. Proactivité Contrôlée

Le systeme ne se contente pas de rapporter:

- il recommande d'augmenter le budget;
- il deplace le contenu vers ce qui fonctionne;
- il cree/prepare PR;
- il resout automatiquement certains tickets;
- il escalade quand il ne sait pas.

Implication ATHOS:

- Athos doit proposer action + raison + preuve + niveau de confiance;
- actions risquées: permission;
- actions reversible/lecture: possible auto-execution;
- actions business: recap et demande de validation si impact financier.

### 6. Feedback Audio Court

Le style visible dans les sous-titres est bref et operatoire:

- "Checking now"
- "Congratulations, sir"
- "My recommendation..."
- "PR is ready whenever you are"

Implication ATHOS:

- pas de longues explications vocales;
- voix = statut, decision, alerte, recommandation;
- detail = UI/log/Room.

## Gaps ATHOS Actuels Face A Cette Reference

1. ATHOS a la Room, mais pas encore le command center metier plein ecran.
2. ATHOS a des moteurs, mais pas une crew de sous-agents roles orientee business.
3. ATHOS a des protocoles nommes, mais ils restent encore trop declaratifs.
4. ATHOS n'a pas encore de dashboard projet connecte aux sources business.
5. ATHOS ne peut pas encore executer un pipeline complet "analytics -> decision -> action -> PR -> recap" sans intervention.
6. Le vocal ATHOS est aujourd'hui moins prioritaire, mais il devra servir de couche de feedback courte.

## Roadmap A Ajouter

### P0.5 — HUD Command Center

- Vue principale:
  - noyau central statut;
  - Room compacte;
  - agents actifs;
  - actions en cours;
  - derniers blocages;
  - health runtime;
  - projets suivis.
- Aucun effet visuel gratuit: chaque widget doit porter une information operationnelle.

### P1 — Crew ATHOS

- Roles initiaux:
  - Operator: orchestration et recap;
  - Dev: code/test/PR;
  - Growth: ads, acquisition, contenu;
  - Support: tickets, emails, escalade;
  - Analyst: metriques, anomalies, recommandations;
  - Archivist: Drive, memoire, provenance.
- Chaque role mappe vers moteur/skill/source selon disponibilite.

### P1 — Project Telemetry Registry

- Objet `Project`:
  - sources;
  - metriques;
  - seuils;
  - routines;
  - risques;
  - prochaine action.
- Premier usage: Ex-Nihilo + projets clients autorises.

### P1/P2 — Protocoles Metier Executables

- `ATHOS_GROWTH_REVIEW`
- `ATHOS_CLIENT_DAILY`
- `ATHOS_CREATIVE_PIPELINE`
- `ATHOS_DEV_HANDOFF`
- `ATHOS_SUPPORT_TRIAGE`

Chaque protocole:

- entree vocale/texte;
- sources consultees;
- agents roles;
- droits requis;
- actions possibles;
- checkpoints;
- recap final.

### P2 — Actions Multi-Outils

- Slack/Teams/Gmail/Drive/GitHub/Shopify/analytics/ads.
- Garde-fou: lecture par defaut, mutation avec scopes et validation.

## Phrase Directrice

Athos ne doit pas seulement repondre. Athos doit tenir une salle de controle, suivre des systemes reels, deleguer a des agents roles, prendre des decisions situees, agir quand c'est reversible, demander validation quand c'est risqué, puis recapitulrer en une phrase.
