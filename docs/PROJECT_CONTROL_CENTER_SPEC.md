# ATHOS — Project Control Center (PCC)
# Spécification Produit Complète

**Version** : 1.0 | **Date** : 2026-05-20 | **Scope** : Claude (frontend) + Codex (backend)
**Priorité** : P2 | **Statut** : Frontend prototype en cours — backend à brancher

---

## 1. Finalité

### Pourquoi ce module existe

Le dashboard ATHOS actuel traite SEO, Finances, Commandes, CRM comme des pages **globales**.
Le Project Control Center transforme ATHOS en **ERP multi-projets** : chaque entité business devient une unité pilotable.

**Avant PCC** : "voici les stats SEO de l'agence"
**Après PCC** : "voici les stats SEO de Rouge Pivoine, liées à son repo, son Shopify, ses agents IA dédiés, ses objectifs CA, et ses alertes actives"

### Ce que PCC rend possible

1. **Chaque projet est une entité cohérente** — identité, outils, agents, KPIs, roadmap
2. **ATHOS devient multi-client** — supervision simultanée de N projets
3. **Les pages business deviennent contextuelles** — SEO de Rouge Pivoine ≠ SEO de Placerr
4. **Les agents IA sont assignés à des projets** — pas juste disponibles globalement
5. **Les intégrations sont documentées et vérifiées** — état connecté/KO visible
6. **La Room se contextualise** — débattre d'un problème lié à un projet précis

---

## 2. Modèle fonctionnel

### Un projet ATHOS contient

```typescript
interface ATHOSProject {
  // Identité
  id: string;
  name: string;
  type: ProjectType;        // shopify | saas | mobile | site | agency | other
  description?: string;
  status: ProjectStatus;    // active | building | pending | done | paused
  priority: number;         // 0 = P0 critique, 5+ = backlog
  owner?: string;
  created_at: string;
  updated_at: string;

  // Présence numérique
  domains?: string[];
  sites?: SiteRef[];
  repos?: RepoRef[];
  drives?: DriveRef[];

  // Outils business (Integration Registry)
  integrations: Integration[];

  // Réseaux sociaux (Social Channel Registry)
  channels: SocialChannel[];

  // Agents IA dédiés
  agents: ProjectAgent[];

  // Objectifs et KPIs
  goals: ProjectGoal[];
  kpis?: ProjectKPI[];

  // Activité
  tasks?: TaskRef[];
  roadmap?: RoadmapItem[];
  memory_ref?: string;      // chemin vers fichier .mem dédié
  recent_activity?: ActivityEntry[];

  // Alertes
  alerts?: ProjectAlert[];
  blockers?: string[];
  next_actions?: string[];
}
```

### Types de projets supportés

| Type | Description | Exemples |
|------|-------------|---------|
| `shopify` | Boutique e-commerce Shopify | Rouge Pivoine, Olivia |
| `saas` | Application SaaS | Placerr |
| `mobile` | Application mobile (React Native, Expo) | MeetMe, Nearby |
| `site` | Site vitrine / agence | ex-nihilo.agency |
| `agency` | Meta-projet agence | Ex-Nihilo Agency |
| `other` | Autre | — |

### Statuts projets

| Statut | Couleur | Description |
|--------|---------|-------------|
| `active` | green | En production ou développement actif |
| `building` | accent | En construction initiale |
| `pending` | border | En attente de démarrage |
| `paused` | yellow | Suspendu temporairement |
| `done` | muted | Terminé, archivé |

---

## 3. UX attendue — vues

### 3.1 — Liste projets (enrichie)

**Route** : `/dashboard/projects` (existante — à enrichir)

Évolutions P2 :
- CTA "Créer un projet" →  `/dashboard/projects/new`
- Liens vers détail projet → `/dashboard/projects/[id]`
- Filtres : statut, type, priorité
- Vue cards améliorée (score santé, intégrations count, alertes)
- KPI grid existant conservé

### 3.2 — Détail projet

**Route** : `/dashboard/projects/[projectId]`

Sections :
1. **Header** — nom, type, statut, priorité, actions
2. **Santé générale** — score composite, alertes actives, blockers
3. **Présence numérique** — sites, domaines, repos, Drive
4. **Outils connectés** — intégrations état connecté/KO
5. **Réseaux sociaux** — channels configurés, stats résumées
6. **Agents IA** — agents assignés, dernière activité
7. **Objectifs & KPIs** — progression vers les goals
8. **Roadmap projet** — prochaines actions, tickets
9. **Mémoire récente** — dernières entrées §-format
10. **Alertes projet** — bloqueurs, avertissements

### 3.3 — Wizard création projet

**Route** : `/dashboard/projects/new`

7 étapes linéaires avec navigation précédent/suivant :

#### Étape 1 — Identité
- Nom du projet (required)
- Type de projet (select)
- Description (optionnel)
- Statut initial (active / pending / building)
- Priorité (P0 à P5)

#### Étape 2 — Présence numérique
- Site web (URL)
- Domaine principal
- Repository GitHub (URL)
- Dossier Google Drive (URL ou path)

#### Étape 3 — Outils business
- Shopify (store URL)
- Stripe (présent ou non)
- Google Analytics (ID)
- Google Search Console (property)
- CRM (type + référence)
- Hébergement (provider + URL)
- Monitoring (endpoint)

#### Étape 4 — Réseaux sociaux
- Instagram (handle)
- TikTok (handle)
- LinkedIn (URL)
- X / Twitter (handle)
- YouTube (channel URL)
- Facebook (page URL)
- Pinterest (handle)
- Newsletter (provider + liste)

#### Étape 5 — Objectifs
- CA mensuel cible (€)
- Trafic organique cible (visites/mois)
- Leads mensuels cibles
- Commandes mensuelles cibles
- Positions SEO cibles (top 10 : N mots-clés)
- Cadence contenu (posts/semaine)

#### Étape 6 — Agents ATHOS
- SEO Agent (toggle + degré autonomie)
- Dev Agent (toggle + degré autonomie)
- Finance Agent (toggle + degré autonomie)
- Content Agent (toggle + degré autonomie)
- Automation Agent (toggle + degré autonomie)

#### Étape 7 — Récapitulatif
- Aperçu complet du projet
- Badges : type, statut, priorité
- Intégrations configurées (count)
- Réseaux configurés (count)
- Agents assignés (count)
- Objectifs définis (count)
- Notice prototype frontend
- CTA : "Créer le projet" (→ backend à brancher)

### 3.4 — Gestion des intégrations

Section au sein du détail projet :

Pour chaque intégration :
- Nom et icône de l'outil
- Statut : `connected` | `configured` | `error` | `not_configured`
- URL / référence
- Dernière vérification
- Action : Configurer / Tester / Reconnecter

---

## 4. Données réelles vs prototype

| Données | Statut actuel | Source future |
|---------|---------------|---------------|
| Liste projets (athos_projects.mem) | RÉEL (§-format parsé) | /api/projects enrichi |
| Détail projet | PROTOTYPE (mock statique) | /api/projects/[id] |
| Création projet | PROTOTYPE (local state) | POST /api/projects |
| Intégrations statut | PROTOTYPE (mock) | /api/projects/[id]/integrations |
| Social channels | PROTOTYPE (mock) | /api/projects/[id]/channels |
| Agents assignés | PROTOTYPE (mock) | /api/projects/[id]/agents |
| Goals/KPIs | PROTOTYPE (mock) | /api/projects/[id]/goals |
| Activité récente | PROTOTYPE (mock) | /api/projects/[id]/activity |

---

## 5. Contrats backend proposés — PROPOSAL / À ARBITRER CODEX

### 5.1 — Liste projets enrichie

```
PROPOSAL: POST /api/projects
Body: { "include_details"?: true, "filter_status"?: string, "filter_type"?: string }
Response: {
  "projects": [
    {
      "id": "rouge-pivoine",
      "name": "Rouge Pivoine",
      "type": "shopify",
      "status": "active",
      "priority": 5,
      "integrations_count": 3,
      "integrations_ok": 2,
      "alerts_count": 1,
      "health_score": 0.72,
      "next_action": "Push thème draft sur GitHub",
      // + champs existants §-format
    }
  ],
  "total": 7,
  "active": 4
}
```

### 5.2 — Détail projet

```
PROPOSAL: POST /api/projects/detail
Body: { "id": "rouge-pivoine" }
Response: {
  "project": {
    "id": "rouge-pivoine",
    "name": "Rouge Pivoine",
    "type": "shopify",
    "status": "active",
    "priority": 5,
    "description": "...",
    "domains": ["rouge-pivoine.fr"],
    "repos": [{ "url": "https://github.com/exnihilo042/rouge-pivoine-theme", "branch": "main" }],
    "integrations": [
      { "tool": "shopify", "status": "connected", "ref": "rouge-pivoine.myshopify.com" },
      { "tool": "github", "status": "connected", "ref": "rouge-pivoine-theme" },
      { "tool": "gsc", "status": "not_configured", "ref": null }
    ],
    "channels": [
      { "platform": "instagram", "handle": "@rougepivoine", "configured": true }
    ],
    "agents": [
      { "role": "dev", "engine": "claude_code", "last_activity": "2026-05-20T10:00:00" }
    ],
    "goals": [
      { "type": "ca_monthly", "target": 2000, "current": 1200, "unit": "€" }
    ],
    "next_actions": ["Push thème sur GitHub", "Valider avec client"],
    "blockers": [],
    "memory_ref": "memory/rouge_pivoine.mem"
  }
}
```

### 5.3 — Création projet

```
PROPOSAL: POST /api/projects/create
Body: {
  "name": "Rouge Pivoine",
  "type": "shopify",
  "status": "active",
  "priority": 5,
  "description": "...",
  "domains": ["rouge-pivoine.fr"],
  "integrations": [...],
  "channels": [...],
  "goals": [...]
}
Response: { "id": "rouge-pivoine", "created": true }
```

### 5.4 — Update projet

```
PROPOSAL: POST /api/projects/update
Body: { "id": "rouge-pivoine", "fields": { "status": "done", "priority": 6 } }
Response: { "updated": true }
```

### 5.5 — Agents projet

```
PROPOSAL: POST /api/projects/agents
Body: { "project_id": "rouge-pivoine" }
Response: {
  "agents": [
    { "role": "seo", "engine": "claude_code", "autonomy": "supervised", "last_activity": "..." }
  ]
}
```

### 5.6 — Goals & KPIs

```
PROPOSAL: POST /api/projects/goals
Body: { "project_id": "rouge-pivoine" }
Response: {
  "goals": [
    { "type": "ca_monthly", "target": 2000, "current": 1200, "unit": "€", "trend": "up" },
    { "type": "traffic", "target": 5000, "current": 3800, "unit": "visites/mois", "trend": "stable" }
  ]
}
```

---

## 6. Plan de réalisation

### Phase 1 — Frontend prototype (Claude, session courante)

- [x] Liste projets enrichie avec CTA "Créer"
- [x] Page détail projet prototype (mock)
- [x] Wizard création 7 étapes (client component)
- [x] Composants UI : IntegrationBadge, WizardStepHeader, SocialChannelPill, ProjectSection

### Phase 2 — Backend persistance (Codex, dès disponible)

- [ ] /api/projects enrichi (liste avec health_score, integrations_count)
- [ ] /api/projects/detail (fiche complète)
- [ ] /api/projects/create (persistance §-format dans .mem)
- [ ] /api/projects/update
- [ ] /api/projects/agents
- [ ] /api/projects/goals

### Phase 3 — Intégrations réelles (Codex + Claude)

- [ ] Vérification connexion Shopify (health check API)
- [ ] Vérification connexion GitHub (repo accessible)
- [ ] Vérification GSC (property configurée)
- [ ] Stats réelles par projet (CA, trafic, positions)

### Phase 4 — Contextualisation globale (Claude)

- [ ] Pages SEO / Finances / Commandes filtrables par projet
- [ ] Room contextuelle par projet
- [ ] Agents dédiés par projet dans le graphe de capacités

---

## 7. Composants UI créés

| Composant | Usage | Fichier |
|-----------|-------|---------|
| `IntegrationBadge` | Statut outil (connected/error/not_configured) | components/ui/index.tsx |
| `WizardStepHeader` | Indicateur étapes wizard | components/ui/index.tsx |
| `SocialChannelPill` | Affichage réseau social configré | components/ui/index.tsx |
| `ProjectSection` | Wrapper de section dans détail projet | components/ui/index.tsx |

---

## 8. Ce qui reste à Codex

1. Backend persistance projets (§-format enrichi dans .mem ou SQLite)
2. API /api/projects CRUD complet
3. Health check des intégrations (Shopify, GitHub, GSC...)
4. Agrégation stats réelles par projet (CA → Shopify, Trafic → GSC, Positions → GSC)
5. Agents projet liés au graphe de capacités
6. Goals / KPIs calculés depuis les vraies sources

---

## Ancre anti-oubli

> Le PCC transforme ATHOS de "dashboard d'observation" en "ERP IA pilotable".
> Sans PCC, les pages SEO, Finances, Commandes n'ont pas de contexte projet.
> Avec PCC, chaque dollar, chaque visite, chaque commit est rattaché à un projet précis.
