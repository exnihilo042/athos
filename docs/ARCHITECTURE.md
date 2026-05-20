# ATHOS — Architecture Technique

**Version** : 0.8 | **Date** : 2026-05-20

---

## 1. Vue d'ensemble

ATHOS est structuré en trois couches :

```
┌─────────────────────────────────────────────────────┐
│  PRÉSENTATION (Claude)                              │
│  dashboard/ — Next.js 16, App Router, TypeScript    │
│  voice/index.html — PWA voix                        │
├─────────────────────────────────────────────────────┤
│  ORCHESTRATION (Codex + Claude)                     │
│  voice/server.py — HTTP pur, délègue à core/        │
│  core/athos_engine.py — super_LLM_respond           │
│  core/athos_router.py — routing + failover          │
├─────────────────────────────────────────────────────┤
│  RUNTIME CORE (Codex)                               │
│  core/task_queue.py — queue persistante             │
│  core/session_kernel.py — JSONL events              │
│  core/athos_room.py — SQLite Room                   │
│  core/memory_manager.py — read/write §-mem          │
└─────────────────────────────────────────────────────┘
```

---

## 2. voice/server.py

**Rôle** : HTTP pur. Reçoit les requêtes, délègue 100% à `core/`.

**Classe** :
```python
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
```
→ Chaque requête dans son propre thread. Concurrent requests OK.

**Routes principales** (toutes POST sauf SSE) :
| Route | Scope | Statut |
|-------|-------|--------|
| /api/status | read | ✅ |
| /api/observability | read | ✅ |
| /api/conversation | read/write | ✅ |
| /api/message | write | ✅ |
| /api/events | SSE | ✅ |
| /api/capability_graph | read | ✅ |
| /api/projects | read (mem) | ✅ |
| /api/settings | read | ✅ |
| /api/tasks | read/write | ✅ |
| /api/memory/note | write | ✅ |
| /api/stream | SSE voix | ✅ |

---

## 3. Dashboard Next.js

**Stack** : Next.js 16.2.6 / React 19 / TypeScript / Tailwind (tokens uniquement)
**Port** : 3333 (via 9router proxy)
**Pattern** : App Router, Server Components + Client Components

**Routes** (v4 — 19 routes) :
```
/dashboard/hub          → Vue Centrale — MIXTE  (KPIs réels + modules nav)
/dashboard/room         → Room multi-IA — RÉEL  (client: RoomClient.tsx + SSE)
/dashboard/agents       → Capability Graph — RÉEL
/dashboard/alerts       → Alertes système — RÉEL (/api/observability)
/dashboard/automations  → Automations — RÉEL  (contrôles disabled → Codex)
/dashboard/reports      → Rapports — RÉEL  (4 sections CODEX en attente)
/dashboard/projects     → Sites & Projets — RÉEL (/api/projects, parse mem)
/dashboard/settings     → Paramètres — RÉEL (/api/settings, /api/security)
/dashboard/performance  → Performance — MIXTE (santé RÉEL, Lighthouse MOCK)
/dashboard/crm          → CRM / Clients — MOCK (/api/crm non implémenté)
/dashboard/finances     → Finances — MOCK (Stripe/Shopify à connecter)
/dashboard/commandes    → Commandes — MOCK (Shopify Admin API)
/dashboard/seo          → SEO Analytics — MOCK (GSC API)
/dashboard/roadmap      → Roadmap — STATIQUE
/api/athos-proxy        → POST proxy vers HUB avec auth (server-side token)
/api/athos-events       → SSE proxy vers /api/events HUB
```

**Design system** : `dashboard/components/ui/index.tsx`
Composants : Card, StatCard, Badge, EngineBadge, SectionLabel, DataRow, MockBanner, BarChart, Gauge, PageHeader, StatusDot, RealityBadge, EmptyPanel

**Séparation** : Server Components pour fetch ATHOS, Client Components pour SSE/interactif (Room, TopBar).

**Sécurité** : ATHOS_TOKEN côté serveur uniquement. Jamais exposé au client. `/api/athos-proxy` valide que l'endpoint commence par `/api/`.

---

## 4. Séparation Claude / Codex

| Périmètre Claude | Périmètre Codex |
|-----------------|----------------|
| dashboard/ | core/task_queue.py |
| components/ | core/athos_engine.py (deep) |
| lib/ui, lib/charts | responders runtime |
| docs/ | workers background |
| parsing .mem (frontend) | retry moteur logic |
| SSE proxy Next.js | session_writer.py E2E |
| design system | orchestration autonome |

**Règle absolue** : Si le bug nécessite de toucher `core/task_queue.py` ou les responders moteurs, c'est Codex. Si c'est la présentation ou l'UX, c'est Claude.

---

## 5. SSE — Flux temps réel

```
Navigateur
  ↓ GET /api/athos-events  (Next.js, streaming)
  ↓ POST /api/events       (ATHOS HUB)
  ↓ tail athos_session_kernel.jsonl (1s poll)
  ↓ heartbeat 30s

Événements émis :
  event: status      → snapshot AthosStatus complet
  event: session_event → ligne JSONL kernel
  event: heartbeat   → {ts, server: "athos"}
  event: error       → {error: string}
```

**Reconnexion** : EventSource natif + retry manuel à 10s (TopBar), 8s fallback poll (Room).

---

## 6. Mémoire — Format §

```
§clé:valeur|champ2:val2|champ3:val3
```

**Règles** :
- Jamais de prose dans les .mem
- Pipe comme séparateur de champs
- Sous-champs avec `_` au lieu d'espaces
- Arrays avec `[elem1,elem2]`
- Sections avec commentaires `# ──`

**Écriture** : uniquement via `memory_manager.write_session()` ou `/api/memory/note`.
**Lecture** : directe (fichier texte) ou via API server.

---

## 7. Tests

**Exécution** : `source venv/bin/activate && python -m pytest tests/ -q`
**Résultats actuels** : 194 tests passing
**CI** : GitHub Actions sur push (`.github/workflows/`)
**Scope** : core/ uniquement. Le dashboard n'a pas de tests automatiques.
