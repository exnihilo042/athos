# ATHOS — Spécification Système

**Version** : 0.8 | **Date** : 2026-05-20 | **Source** : Claude Sonnet 4.6

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
| Dashboard Next.js | ✅ RÉEL | Port 3333, 19 routes — v4 |
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

## 6. Règles non négociables

1. Ne jamais committer sans demande explicite de Clément
2. Ne jamais logger ou exposer ATHOS_ACCESS_TOKEN
3. CORS strict : `localhost` uniquement sur :7474
4. Zéro dépense API payante par défaut
5. Tout changement durable → Drive + GitHub + tests
6. Co-author git : `Jerykko/Ex-nihilo <contact@ex-nihilo.agency>`
