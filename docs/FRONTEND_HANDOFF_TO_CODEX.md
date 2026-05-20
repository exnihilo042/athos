# ATHOS Dashboard — Frontend Handoff to Codex

**Version** : 1.2 | **Date** : 2026-05-21
**Auteur** : Claude (dashboard scope)
**Destinataire** : Codex (runtime/backend scope)

---

## Contexte

Le dashboard ATHOS v9 (runtime binding) est branché sur les endpoints Codex livrés.
Ce document liste l'état actuel de chaque endpoint — livré ou encore à faire.

**Règle absolue de scope** : Claude ne touche pas `core/`, `voice/`, responders, router, workers, hooks, scripts.
Codex ne touche pas `dashboard/`, `docs/` (sauf ce backlog).

---

## ✅ Endpoints Codex livrés — consommés par le dashboard

| Endpoint | Page | Statut frontend |
|----------|------|-----------------|
| `POST /api/autonomous_loop` | Automations | RÉEL — contrôles start/stop/pause/reset actifs |
| `POST /api/tasks` | Automations | RÉEL — liste + contrôles pause/resume/retry/cancel |
| `POST /api/conversation { action: "health" }` | Reports | RÉEL — session health, task summary |
| `POST /api/report { type: "daily" }` | Reports | RÉEL — brief, sections, summary |
| `POST /api/performance` | Performance | RÉEL — latences mesurées, Lighthouse vide (non configuré) |
| `POST /api/crm` | CRM | RÉEL PARTIEL — extraction athos_projects.mem |

---

## 1. Lighthouse — P1 (bloquant visuel)

### /api/performance → lighthouse

Page : `/dashboard/performance`
Status actuel : `capabilities.lighthouse_configured=false` → section vide propre

**Ce que Codex doit faire** :
Quand Lighthouse CLI est installé, peupler le champ `lighthouse[]` dans `performance_payload()`.

```python
# core/dashboard_runtime.py
def performance_payload():
    ...
    "lighthouse": run_lighthouse_cli(sites=["ex-nihilo.agency", ...]),  # à implémenter
    "capabilities": { ..., "lighthouse_configured": True },
```

Interface TypeScript : `LighthouseResult` dans `dashboard/lib/types.ts`

Le frontend affichera automatiquement les scores quand le champ est non-vide.

---

## 2. Endpoints encore à faire — P2

### /api/crm → enrichissement

Page : `/dashboard/crm`
Status actuel : **RÉEL PARTIEL** — extraction athos_projects.mem · `data_quality: "partial"`

Données manquantes selon le backend :
- `monthly_value` par client
- `historique relationnel structuré`
- `CRM dédié`

Pour enrichir, ajouter ces infos dans `core/dashboard_runtime.py → _project_to_client()` ou connecter un outil CRM.

Interface TypeScript : `CrmRuntimePayload`, `CrmClientRuntime` dans `dashboard/lib/types.ts`

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
`pause` : livré côté backend ✅
`reset` : remet `iterations` et `idle_ticks` à 0 ✅

**Status 2026-05-21** : ✅ LIVRÉ — contrôles actifs dans `AutomationControlsClient.tsx`

---

### Contrôles tâches

Page : `/dashboard/automations` (section Task Queue)
**Status 2026-05-21** : ✅ LIVRÉ — `/api/tasks { action, task_id }` consommé. Boutons pause/resume/retry/cancel actifs par tâche.

---

## 4. Rapport daily — ✅ LIVRÉ

Page : `/dashboard/reports`
**Status 2026-05-21** : ✅ RÉEL — brief, sections, summary depuis `/api/report { type: "daily" }`

**Types de rapport encore à implémenter (Codex P3)** :
```
POST /api/report { "type": "actions" }    → liste actions autonomes par session
POST /api/report { "type": "weekly" }     → agrégat 7 jours
POST /api/report { "type": "costs" }      → budget par moteur
POST /api/report { "type": "export", "format": "md|json" }
```

---

## 5. Session health — ✅ LIVRÉ

Page : `/dashboard/reports`
**Status 2026-05-21** : ✅ RÉEL — `/api/conversation { action: "health" }` retourne `active_sessions`, `total_messages`, `summary` (task counts).

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
| `AutonomousLoopPayload` | ✅ RÉEL (v9) | Automations |
| `BackendTask`, `TaskListPayload` | ✅ RÉEL (v9) | Automations |
| `PerformanceRuntimePayload` | ✅ RÉEL (v9) | Performance |
| `CrmRuntimePayload`, `CrmClientRuntime` | ✅ RÉEL PARTIEL (v9) | CRM |
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

## 9. Commande de vérification build

Après chaque implémentation Codex, vérifier que le dashboard compile :

```bash
cd ~/Sites/athos/dashboard && npx next build
```

Résultat attendu : 22+ routes, 0 erreur TypeScript.

---

## 11. Skills & Capacités — Statique, scope P3

**Page** : `/dashboard/skills` — données 100% statiques depuis `dashboard/lib/skill-registry.ts`

### Ce que Claude a fait (dashboard v8, scope Claude uniquement)
- `dashboard/lib/skill-registry.ts` : types, 47 skills, SKILL_CATEGORIES, ATHO_AGENTS, SKILL_WORKFLOWS, SKILL_STATS
- `dashboard/app/dashboard/skills/page.tsx` : server component, passe props à SkillsClient
- `dashboard/components/SkillsClient.tsx` : filtres multi-critères, cards expand/collapse, RecommendationEngine, AgentSkillMatrix
- `dashboard/components/ui/index.tsx` : `SkillCategoryBadge`, `SkillMaturityBadge` exportés
- Navigation, Hub ModuleCard/ProductRow, Agents lien, Automations lien — tous intégrés

### Ce que Codex devra faire en P3 (pas avant)

```
POST /api/skills/registry    → liste enrichie avec last_used, call_count, installed: boolean
POST /api/skills/recommend   → recommandation contextuelle {context, phase, agent}
POST /api/skills/execute     → déclenche un skill depuis ATHOS HUB
POST /api/skills/log         → historique d'usage skill
```

**Voir** : `docs/SKILL_REGISTRY_SPEC.md` section 6 et `docs/API_CONTRACTS.md` section "Skills Registry API".

**Important** : ne pas toucher `skill-registry.ts` ni `SkillsClient.tsx` tant que les endpoints P3 ne sont pas implémentés. Le frontend consommera les endpoints et remplacera les données statiques à ce moment-là.
