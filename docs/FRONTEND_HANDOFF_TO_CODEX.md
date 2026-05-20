# ATHOS Dashboard — Frontend Handoff to Codex

**Version** : 1.2 | **Date** : 2026-05-20
**Auteur** : Claude (dashboard scope)
**Destinataire** : Codex (runtime/backend scope)

---

## Contexte

Le dashboard ATHOS v5 est maintenant à jour côté frontend.
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

> **Note tracking** : `dashboard/lib/` était ignoré par un pattern `lib/` Python dans le root `.gitignore`.
> Corrigé en v5 : ajout de `!dashboard/lib/` et `!dashboard/lib/**` à la fin du `.gitignore` racine.
> `dashboard/lib/types.ts` et `dashboard/lib/athos.ts` sont désormais tracké dans git.

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

## 8. Convention InsetNotice — endpoints non implémentés

Chaque page attendant un endpoint Codex affiche maintenant un `<InsetNotice>` en haut de page.
Format standardisé :
```tsx
<InsetNotice
  icon="◱"
  text="Endpoint /api/X non implémenté"
  detail="Interface TypeScript : XPayload dans dashboard/lib/types.ts · Scope Codex P2"
  variant="muted"
/>
```

Supprimer l'`InsetNotice` et le `MockBanner` associés dès que l'endpoint est opérationnel, puis changer les données.

---

## 9. Project Control Center — Backend à prévoir (PRIORITÉ P2)

> Spécification complète : `docs/PROJECT_CONTROL_CENTER_SPEC.md`
> Contrats API détaillés : `docs/API_CONTRACTS.md` (section PCC)

### Pages frontend existantes (prototype mockées)

| Page | Route | Données actuelles | Backend requis |
|------|-------|-------------------|----------------|
| Liste projets enrichie | /dashboard/projects | /api/projects (§-format, existant) | Enrichissement : health_score, integrations_count, alerts_count |
| Wizard création projet | /dashboard/projects/new | Local state uniquement (prototype) | POST /api/projects/create |
| Détail projet | /dashboard/projects/[id] | Mock statique (rouge-pivoine, placerr) | POST /api/projects/detail |

### Endpoints à créer

1. **POST /api/projects/detail** — fiche projet complète (integrations, channels, agents, goals, tasks)
2. **POST /api/projects/create** — persister un projet depuis le wizard (§-format dans .mem ou SQLite)
3. **POST /api/projects/update** — modifier statut, priorité, champs d'un projet
4. **POST /api/projects/agents** — agents IA dédiés par projet
5. **POST /api/projects/goals** — objectifs et KPIs calculés

### Enrichissement /api/projects existant

La route `/api/projects` existe et parse athos_projects.mem.
Ajouter dans la réponse :
- `health_score` (0-1) — composite basé sur integrations + alerts + blockers
- `integrations_count` + `integrations_ok` — depuis fiche projet
- `alerts_count` — alertes actives
- `next_action` — prochaine action extraite du §-format `next:`

### Ce qui est prototype frontend et restera prototype jusqu'au backend

- Données de détail projet (integrations, channels, agents, goals) : **mockées**
- Création projet via wizard : **local state seulement, aucun POST**
- Score santé projet : **mockée**

### Ce qui est déjà réel

- Liste projets depuis athos_projects.mem : **RÉEL**
- KPI counts (actifs/bloqués/en attente/terminés) : **RÉEL**
- Liens vers fiche détail : **fonctionnels pour rouge-pivoine et placerr**

---

## 10. Room multi-IA — Backend à prévoir (PRIORITÉ P1)

> Frontend Room v7 livré et fonctionnel. Les fonctionnalités suivantes nécessitent un backend Codex.
> Contrats API détaillés : `docs/API_CONTRACTS.md` (section "Room multi-IA Enrichie — Backend futur")

### Ce qui est 100% frontend (ne nécessite PAS de backend)

| Fonctionnalité | Implémentation |
|----------------|----------------|
| Recherche full-text | `filterText` sur les 60 messages locaux via `useMemo` |
| Filtres acteurs | Pills toggleables, `Set<string>`, `useMemo` |
| Filtres types | Pills toggleables, `Set<string>`, `useMemo` |
| War Room mode visuel | `warRoomMode` state, CSS box-shadow + border |
| Sidebar collapsible | `showSidebar` state, 254px drawer |
| Roster acteurs (statut local) | Calculé depuis timestamps du thread local |
| Contexte projet (sélecteur) | Local state, données hardcodées — prototype |
| Rendu message spécialisé | Par type : checkpoint/error/report/summary/message |
| Pagination notice (>60) | Notice jaune si `total > thread.length` |

### Ce qui nécessite un backend Codex

| Fonctionnalité | Endpoint requis | Priorité |
|----------------|-----------------|----------|
| Fil par projet (`project_id`) | `POST /api/conversation` avec `project_id` | P1 |
| Historique paginé (>60 msgs) | `POST /api/conversation` avec `offset` | P1 |
| Recherche sur historique complet | `POST /api/conversation/search` | P1 |
| Filtres acteur/type backend | `POST /api/conversation` avec `actor`, `type` | P1 |
| Statut acteur réel (décompte total) | `POST /api/conversation/actors` | P2 |
| Tags manuels sur messages | `POST /api/conversation/tag` | P2 |

### Modification /api/message requise

Pour lier les messages à un projet, enrichir le body :

```json
{ "actor": "clement", "content": "...", "type": "message", "project_id": "rouge-pivoine" }
```

Le frontend `ProjectContextCard` envoie déjà ce champ quand un projet est sélectionné. Le backend doit le persister dans le kernel JSONL.

### Interface TypeScript Room déjà en place

`RoomEntry` dans `dashboard/lib/types.ts` est prêt pour les champs enrichis :
- `project_id?: string` — à utiliser quand le backend persiste ce champ
- `tags?: string[]` — à utiliser quand `/api/conversation/tag` est implémenté

---

## 11. Skill Registry — Note backend (P3)

> Spécification complète : `docs/ATHOS_SPEC.md` section 7

Le Skill Registry est un futur sous-système (P3 — après PCC). Il ne nécessite pas d'endpoint backend immédiat.

Quand le développement commence, les endpoints requis seront :

```
POST /api/skills/list     → catalogue avec statut installé/obsolète + stats usage
POST /api/skills/suggest  → recommandation contextuelle basée sur projet actif + contexte Room
POST /api/skills/stats    → agrégat depuis ~/.gstack/analytics/skill-usage.jsonl
```

La page dashboard `/dashboard/skills` (scope Claude P3) sera construite dès que ces endpoints existent.

---

## 12. Commande de vérification build

Après chaque implémentation Codex, vérifier que le dashboard compile :

```bash
cd ~/Sites/athos/dashboard && npx next build
```

Résultat attendu : 21+ routes (incluant PCC), 0 erreur TypeScript.
