# ATHOS Dashboard — Frontend Handoff to Codex

**Version** : 1.0 | **Date** : 2026-05-20
**Auteur** : Claude (dashboard scope)
**Destinataire** : Codex (runtime/backend scope)

---

## Contexte

Le dashboard ATHOS v4 est maintenant à jour côté frontend.
Ce document liste tout ce que Codex doit implémenter ou valider pour que les pages passent de MOCK/STATIQUE à RÉEL.

**Règle absolue de scope** : Claude ne touche pas `core/`, `voice/`, responders, router, workers, hooks, scripts.
Codex ne touche pas `dashboard/`, `docs/` (sauf ce backlog).

---

## 1. Endpoints manquants — P1 (bloquants visuellement)

### /api/performance

Page : `/dashboard/performance`
Status actuel : Lighthouse et latences affichés en MOCK

**Contrat attendu** :
```
POST /api/performance
Body: {}
```

Réponse attendue :
```json
{
  "lighthouse": [
    { "site": "ex-nihilo.agency", "perf": 74, "a11y": 89, "seo": 92, "bp": 83, "mobile": 62 }
  ],
  "api_latencies": [
    { "endpoint": "/api/status", "p50": 45, "p95": 120, "ok": true }
  ]
}
```

Interface TypeScript : `PerformancePayload` dans `dashboard/lib/types.ts`

Sources suggérées : Lighthouse CLI (`lighthouse --output json`), mesures internes du HUB.

---

## 2. Endpoints manquants — P2

### /api/crm

Page : `/dashboard/crm`
Status actuel : 100% MOCK (4 clients hardcodés)

**Contrat attendu** :
```
POST /api/crm
Body: {}
```

Réponse :
```json
{
  "clients": [
    {
      "id": "uuid",
      "name": "Rouge Pivoine",
      "status": "active",
      "attention": "high",
      "project": "Shopify theme",
      "monthly_value": 1200,
      "next_action": "...",
      "tags": ["shopify", "e-commerce"]
    }
  ],
  "pipeline_total": 7800,
  "active": 2,
  "urgent": 1,
  "blocked": 1
}
```

Interface TypeScript : `CrmPayload`, `CrmClient` dans `dashboard/lib/types.ts`

Source suggérée : `athos_projects.mem` (parsing §-format) ou base CRM future.

---

### /api/commandes

Page : `/dashboard/commandes`
Status actuel : MOCK

**Contrat attendu** :
```
POST /api/commandes
Body: { "store"?: "all|ex-nihilo|rouge-pivoine", "limit"?: 50 }
```

Interface TypeScript : `CommandesPayload`, `Order` dans `dashboard/lib/types.ts`

Source suggérée : Shopify Admin API (requiert credentials store).

---

### /api/finances

Page : `/dashboard/finances`
Status actuel : MOCK

Interface TypeScript : `FinancesSummary`, `ProjectRevenue` dans `dashboard/lib/types.ts`

Source suggérée : Shopify Admin API, Stripe API.

---

### /api/seo

Page : `/dashboard/seo`
Status actuel : MOCK

Interface TypeScript : `SeoSite`, `SeoPosition`, `CoreWebVital` dans `dashboard/lib/types.ts`

Source suggérée : Google Search Console API, PageSpeed Insights API.

---

## 3. Contrôles à débloquer (UI déjà construite, boutons disabled)

### Boucle autonome

Page : `/dashboard/automations`
UI existante : Boutons "Démarrer / Arrêter / Pause / Reset compteurs" — tous `disabled`

**Endpoint requis** :
```
POST /api/autonomous_loop
Body: { "action": "start|stop|pause|reset" }
```

`start` : exige `ATHOS_AUTONOMOUS_LOOP_ENABLED=true`
`stop` : idempotent
`pause` : new — non implémenté côté loop
`reset` : remet `iterations` et `idle_ticks` à 0

---

### Contrôles tâches

Page : `/dashboard/automations` (section Task Queue)
UI existante : Zone "pause / retry / cancel / resume" — CodexPendingZone

**Endpoint requis** :
```
POST /api/tasks
Body: { "action": "pause|retry|cancel|resume", "task_id": "uuid" }
```

Transitions valides déjà documentées dans `API_CONTRACTS.md`.

---

## 4. Rapport daily — enrichissement

Page : `/dashboard/reports`
Status actuel : `/api/report { type: "daily" }` répond souvent vide

**Sections attendues dans la réponse** :
```json
{
  "brief": "Rapport ATHOS — 2026-05-20\n...",
  "date": "2026-05-20T08:00:00",
  "sections": [
    { "title": "Session", "content": "..." },
    { "title": "Task queue", "content": "..." },
    { "title": "Failover", "content": "..." }
  ],
  "summary": {
    "total_sessions": 3,
    "total_messages": 47,
    "failovers": 0,
    "actions": 12
  }
}
```

**Nouveaux types de rapport en attente** :
```
POST /api/report { "type": "actions" }    → liste actions autonomes par session
POST /api/report { "type": "weekly" }     → agrégat 7 jours
POST /api/report { "type": "costs" }      → budget par moteur
POST /api/report { "type": "export", "format": "md|json" }
```

---

## 5. Session health — champs manquants

Page : `/dashboard/reports`
Endpoint utilisé : `POST /api/conversation { "action": "health" }`

**Champs actuellement manquants dans la réponse** :
```json
{
  "active_sessions": 2,
  "total_messages": 47,
  "summary": {
    "total": 5, "running": 1, "done": 3, "blocked": 1, "pending": 0
  }
}
```

Si cet endpoint n'existe pas encore, créer ou aliaser depuis `/api/status` (qui expose `session.events`, `session.exchanges`).

---

## 6. Interfaces TypeScript de référence

Fichier : `dashboard/lib/types.ts`

| Interface | Status | Page |
|-----------|--------|------|
| `AthosStatus` | RÉEL | Hub, TopBar |
| `ObservabilityPayload` | RÉEL | Agents, Performance, Alerts |
| `CapabilityGraph` | RÉEL | Agents |
| `RoomEntry`, `RoomThread` | RÉEL | Room |
| `AthosSettings` | RÉEL | Paramètres |
| `Project` | RÉEL | Sites & Projets |
| `Task`, `TaskQueue` | RÉEL (Codex runtime) | Automations |
| `PerformancePayload` | **CODEX P1** | Performance |
| `CrmPayload`, `CrmClient` | **CODEX P2** | CRM |
| `CommandesPayload`, `Order` | **CODEX P2** | Commandes |
| `FinancesSummary` | **CODEX P2** | Finances |
| `SeoSite`, `SeoPosition` | **CODEX P2** | SEO |

---

## 7. Ce qui ne doit PAS être modifié par Codex

- `dashboard/components/ui/index.tsx` — design system, scope Claude
- `dashboard/app/dashboard/**` — pages Next.js, scope Claude
- `dashboard/components/DashboardShell.tsx` — navigation, scope Claude
- `docs/DESIGN_SYSTEM.md` — design tokens et composants, scope Claude
- `docs/FRONTEND_HANDOFF_TO_CODEX.md` — ce document

---

## 8. Commande de vérification build

Après chaque implémentation Codex, vérifier que le dashboard compile :

```bash
cd ~/Sites/athos/dashboard && npx next build
```

Résultat attendu : 19+ routes, 0 erreur TypeScript.
