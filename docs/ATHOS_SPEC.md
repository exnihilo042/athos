# ATHOS — Spécification Système

**Version** : 1.0 | **Date** : 2026-05-20 | **Source** : Claude Sonnet 4.6

---

## 1. Identité

**A.T.H.O.S.** = Autonomous Tactical Heuristic Operating System

Système local d'orchestration multi-IA conçu pour maximiser la production d'une agence web solo (Ex-Nihilo). ATHOS n'est pas un assistant ; c'est un système opérationnel qui achemine les tâches vers les meilleurs moteurs disponibles, maintient une mémoire persistante entre sessions, et expose un dashboard de supervision.

**Principes fondamentaux** :
- Vérité > confort : ATHOS ne flatte pas, ne rassure pas sans fondement
- Zéro dépense API par défaut : tous les moteurs payants désactivés sauf abonnements existants
- Austérité locale : fonctionnel sans réseau, sans capteurs, sans cloud
- Mémoire persistante : toute session contribue à la base de connaissance

---

## 2. État du système au 2026-05-20

### Implémenté et fonctionnel

| Module | Statut | Notes |
|--------|--------|-------|
| HUB HTTP :7474 | ✅ RÉEL | Python HTTPServer + ThreadingMixIn |
| Routeur moteurs | ✅ RÉEL | chatgpt_plus > claude_code > api > local |
| Room multi-IA | ✅ RÉEL | API REST + auto-respond + auto-work |
| Mémoire §-format | ✅ RÉEL | ~/Sites/athos/memory/*.mem |
| Session kernel | ✅ RÉEL | JSONL, 20 events actuels |
| Observabilité | ✅ RÉEL | /api/observability — failover, ports, mémoire |
| Capability graph | ✅ RÉEL | 72 nœuds, 132 edges, score 1.0 |
| Épistémie guard | ✅ RÉEL | Guardrails truth-over-comfort |
| Task queue | ✅ RÉEL | core/task_queue.py, 194 tests |
| Dashboard Next.js | ✅ RÉEL | Port 3333, 19+ routes — v5 |
| SSE live events | ✅ RÉEL | /api/athos-events proxy → /api/events HUB |
| Auth token | ✅ RÉEL | ATHOS_ACCESS_TOKEN, CORS strict |

### Partiel ou en cours

| Module | Statut | Blocage |
|--------|--------|---------|
| session_writer.py | ⚠ PARTIEL | write_session() non appelé par Codex CLI |
| Codex responder | ⚠ BLOQUÉ | ChatGPT Plus usage_limit — attente reset |
| Austere mode | ✅ CONFIRMÉ | austere_mode_ready = true depuis 2026-05-20 |

### Prévu — réservé Codex

| Module | Statut | Périmètre |
|--------|--------|-----------|
| Task queue UI (pause/retry/cancel) | 📋 CODEX | Boutons runtime, pas frontend seul |
| Session writer E2E | 📋 CODEX | Nécessite Codex CLI actif |
| Responders recovery | 📋 CODEX | Orchestration runtime |

### Mock — données fictives

| Module | Statut | Source future |
|--------|--------|---------------|
| Dashboard Finances | 🔸 MOCK | Stripe API / Shopify Admin API |
| Dashboard SEO | 🔸 MOCK | Google Search Console API |
| Dashboard Performance | 🔸 MIXTE | Score santé RÉEL, Lighthouse MOCK → /api/performance (Codex P1) |
| Dashboard CRM | 🔸 MOCK | /api/crm (Codex P2) |
| Dashboard Commandes | 🔸 MOCK | Shopify Admin API (Codex P2) |

---

## 3. Architecture réseau

```
[Clément / Navigateur / iPhone]
         │
         ├── :3333 Next.js Dashboard (9router)
         │       ├── /api/athos-proxy → POST :7474
         │       └── /api/athos-events → SSE :7474/api/events
         │
         ├── :7474 ATHOS HUB (voice/server.py)
         │       ├── /api/status
         │       ├── /api/observability
         │       ├── /api/conversation
         │       ├── /api/message → auto-work + auto-respond
         │       ├── /api/events  (SSE streaming)
         │       ├── /api/projects (parse mem)
         │       ├── /api/settings
         │       └── /api/capability_graph
         │
         ├── :8765 agentmemory (Python)
         └── iPhone/PWA → /api/stream (voix STT+TTS)
```

---

## 4. Moteurs et routage

**Ordre de priorité** : `chatgpt_plus > claude_code > anthropic_api > grok > ollama`

| Moteur | État | Type |
|--------|------|------|
| chatgpt_plus (Codex CLI) | ⚠ usage_limit | Abonnement |
| claude_code | ✅ disponible | Abonnement |
| anthropic_api | ❌ désactivé | Payant (zéro spend) |
| ollama | 🔸 fallback | Local |

---

## 5. Mémoire

**Format** : §-compressé, pipe-séparé, machine-readable
**Stockage canonique** : `~/Sites/athos/memory/`
**Fichiers critiques** :

| Fichier | Contenu |
|---------|---------|
| athos_identity.mem | Persona, user profile, règles globales |
| athos_capabilities.mem | Graphe de capacités complet |
| athos_projects.mem | État temps réel tous projets |
| athos_cognition.mem | Architecture cognitive, boucle reasoning |
| athos_kernel_plan.mem | Plan de reprise, roadmap P0/P1 |
| athos_session_summary.mem | Résumé session courante |

---

## 6. Vision produit — ce qui reste à bâtir

> ATHOS est une fondation, pas un aboutissement. Le dashboard actuel couvre la supervision système.
> Les modules suivants transformeront ATHOS en ERP IA / JARVIS réel.

### Modules manquants pour atteindre la vision

| Module | Priorité | Description |
|--------|----------|-------------|
| Project Control Center | P2 | Gestion ERP multi-projets — frontend prototype en cours |
| Integration Registry | P2 | Outils rattachés par projet (Shopify, Stripe, GSC, GitHub...) |
| Social Channel Registry | P2 | Réseaux sociaux par projet (IG, TikTok, LinkedIn, X...) |
| Project Agents | P2 | Agents IA dédiés par projet avec rôles et permissions |
| Project Goals & KPIs | P2 | Métriques business par projet (CA, trafic, leads...) |
| Room / War Room | P1 | Enrichissement frontend — filtres, sidebar, contexte projet, War Room mode (v7 livré) |
| Skill Registry / Capability Layer | P3 | ATHOS doit connaître ses skills et les recommander au bon moment (voir section 8) |
| Room collaborative | P4 | Vraie war room multi-IA avec débats et consensus — fondations posées en v7 |
| Moteur de proactivité | P4 | Watchtowers business/SEO/infra + alertes prédictives |
| Knowledge Graph | P4 | Graphe structuré projets × clients × outils × événements |
| Voice Layer | P5 | STT/TTS local, wake word, orb ATHOS CORE |
| Edge Agents | P5 | Mac, iPhone, VPS — présence continue multi-device |
| Gouvernance permissions | P5 | Multi-user, audit trail, rôles granulaires |
| Mode Mission Control | P5 | Supervision globale temps réel tous projets |
| Système prédictif | P5 | Anticipe les besoins avant formulation |

---

## 7. Skill Registry / Capability Layer

> Sous-système futur — vision gravée ici pour ne jamais l'oublier.

### Pourquoi ATHOS a besoin d'un Skill Registry

ATHOS orchestre des agents IA. Ces agents disposent de skills opératoires (QA, review, benchmark, design, SEO, ship, scraping...). Sans un registre structuré, ces skills ne sont pas exploités au bon moment : ils existent mais ne sont pas recommandés.

Le Skill Registry est le catalogue vivant de ce qu'ATHOS sait faire opérationnellement — et la couche qui associe les bons skills aux bons moments.

### Catégories de skills à modéliser

| Catégorie | Skills représentatifs |
|-----------|----------------------|
| Sécurité & guardrails | `/careful`, `/guard`, `/cso` |
| Design & UI | `/ui-ux-pro-max`, `/design-review`, `/design-consultation`, `/emil-design-eng` |
| QA & Tests | `/qa`, `/qa-only`, `/browse`, `/canary` |
| Planning & architecture | `/plan-eng-review`, `/plan-ceo-review`, `/autoplan`, `/office-hours` |
| Ship & déploiement | `/ship`, `/land-and-deploy`, `/review` |
| Documentation | `/document-generate`, `/document-release`, `/retro` |
| Contexte & mémoire | `/context-save`, `/context-restore` |
| Scraping & données | `/scrape`, `/skillify` |
| Experts métier | `/shopify-expert`, `/seo-expert` |
| Agents & outillage avancé | `/codex`, `/pair-agent`, `/benchmark-models` |

### Association skills × workflows ATHOS

| Déclencheur | Skill recommandé | Quand |
|-------------|-----------------|-------|
| Gros chantier frontend terminé | `/qa` | Avant commit |
| Avant merge de branche | `/review` | Systématique |
| Après optimisation perf | `/benchmark` | Pour mesurer le gain |
| Avant décision architecture | `/plan-eng-review` | En amont du code |
| Fin de session de travail | `/context-save` | Toujours |
| Avant release UI | `/design-review` | Systématique |
| Problème / erreur inexpliquée | `/investigate` | Sur incident |
| Idée nouvelle | `/office-hours` | Avant de coder |

### Différences conceptuelles importantes

- **Skill Claude disponible aujourd'hui** : outil opératoire installé dans `~/.claude/skills/`, invocable via `/skill-name`
- **Capability ATHOS à modéliser demain** : représentation dans le graphe de capacités (`capability_graph`) avec statut, coût, risque
- **Automation intégrée plus tard** : ATHOS recommande automatiquement le skill dans la Room ou dans un rapport, basé sur le contexte

### Module dashboard futur : "Skills & Capabilities"

Ajouter à terme une page `/dashboard/skills` :
- Catalogue des skills disponibles sur la machine
- Statut : installé / non installé / obsolète
- Statistiques d'usage (depuis `~/.gstack/analytics/skill-usage.jsonl`)
- Recommandations contextuelles basées sur les projets actifs
- Lien vers la documentation de chaque skill

**Priorité** : P3 — après PCC (P2). À inscrire dans la roadmap.

---

## 8. Règles non négociables

1. Ne jamais committer sans demande explicite de Clément
2. Ne jamais logger ou exposer ATHOS_ACCESS_TOKEN
3. CORS strict : `localhost` uniquement sur :7474
4. Zéro dépense API payante par défaut
5. Tout changement durable → Drive + GitHub + tests
6. Co-author git : `Jerykko/Ex-nihilo <contact@ex-nihilo.agency>`
7. Cloisonnement Claude/Codex : dashboard/produit = Claude · runtime/backend = Codex
8. Vérité > confort : ATHOS corrige les biais, sépare faits/inférences/opinions
9. Austérité locale : fonctionnel offline, sans cloud, sans capteurs
10. Toute action : visible, loggée, stoppable, reportée
