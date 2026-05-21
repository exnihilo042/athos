# ATHOS — Codex Runtime Endpoints

Document runtime non conflictuel. Ne décrit que les endpoints backend livrés ou enrichis côté Codex.

## POST `/api/projects`

Retourne la liste enrichie des projets pour le Project Control Center.

### Body
```json
{}
```

### Réponse
```json
{
  "ok": true,
  "projects": [],
  "summary": {
    "total": 0,
    "active": 0,
    "blocked": 0,
    "partial": 0
  },
  "data_quality": "partial"
}
```

### Notes
- Source principale : `memory/athos_projects.mem`
- Registry d'overrides/créations : `memory/athos_project_registry.json`
- Préserve les champs historiques (`status`, `priority`, `stack`, `next`, `blocker`, `store`, `repo`, etc.)

---

## POST `/api/projects/detail`

Retourne une fiche projet détaillée.

### Body
```json
{
  "project_id": "rouge-pivoine"
}
```

### Réponse
```json
{
  "ok": true,
  "project": {
    "id": "rouge-pivoine",
    "name": "Rouge Pivoine",
    "status": "active",
    "priority": "5",
    "priority_label": "P5",
    "domains": [],
    "repositories": [],
    "integrations": [],
    "social_channels": [],
    "agents": [],
    "goals": [],
    "recent_activity": [],
    "memory": {
      "source": "athos_projects.mem",
      "data_quality": "partial"
    }
  },
  "data_quality": "partial"
}
```

### Erreurs
```json
{ "ok": false, "error": "invalid_project_id" }
{ "ok": false, "error": "project_not_found" }
```

---

## POST `/api/projects/create`

Crée un projet pilotable depuis le wizard PCC.

### Body
```json
{
  "project": {
    "name": "Nom projet",
    "type": "internal",
    "description": "...",
    "priority": "P2",
    "status": "active",
    "domains": [],
    "repositories": [],
    "integrations": [],
    "social_channels": [],
    "goals": [],
    "agents": []
  }
}
```

### Réponse
```json
{
  "ok": true,
  "project_id": "nom-projet",
  "project": {},
  "storage": {
    "type": "json_registry",
    "path": "memory/athos_project_registry.json"
  },
  "warnings": []
}
```

### Erreurs
```json
{ "ok": false, "error": "name_required" }
{ "ok": false, "error": "invalid_array_field" }
{ "ok": false, "error": "project_already_exists" }
```

---

## POST `/api/projects/update`

Met à jour les champs sûrs d'un projet, sans modifier brutalement `athos_projects.mem`.

### Body
```json
{
  "project_id": "rouge-pivoine",
  "patch": {
    "status": "paused",
    "priority": "P1",
    "next_action": "Reprendre bientôt"
  }
}
```

### Réponse
```json
{
  "ok": true,
  "project": {},
  "storage": {
    "type": "json_registry",
    "path": "memory/athos_project_registry.json"
  }
}
```

### Limites
- Champs autorisés : `name`, `description`, `status`, `priority`, `next_action`, `domains`, `repositories`, `integrations`, `social_channels`, `goals`, `agents`
- `project_id` inconnu → `project_not_found`

---

## POST `/api/finances`

Endpoint finances honnête, sans chiffres inventés.

### Body
```json
{}
```

### Réponse
- `summary.athos_budget` : issu du runtime local si disponible
- `data_quality` : `partial`
- `warnings` : explicite l'absence de source Stripe / Shopify / fichier manuel

### Limites
- Aucun CA ni marge inventés
- Aucun appel externe sans credentials

---

## POST `/api/seo`

Endpoint SEO honnête basé sur la mémoire projet.

### Body
```json
{}
```

### Réponse
- `sites[]` dérivés des domaines ou stores trouvés dans `athos_projects.mem`
- métriques SEO réelles laissées à `null`
- `data_quality` : `partial`

### Limites
- Pas de Google Search Console / PageSpeed sans credentials
- Pas de ranking fake

---

## POST `/api/commandes`

Endpoint commandes honnête.

### Body
```json
{
  "project_id": "optional",
  "limit": 50
}
```

### Réponse
- `orders: []` si aucune source réelle
- `data_quality` :
  - `empty_no_source`
  - ou `config_only`

### Erreurs
```json
{ "ok": false, "error": "invalid_limit" }
```

---

## POST `/api/skills/registry`

Registry backend statique multi-moteurs.

### Body
```json
{}
```

### Réponse
- `skills[]` : inventaire backend stable
- `summary.total`
- `data_quality: "static_registry"`

### Notes
- Source backend indépendante du frontend `dashboard/lib/skill-registry.ts`
- Inclut le catalogue Codex minimal requis + un subset prudent Claude/ATHOS

---

## POST `/api/skills/engine-availability`

Expose l'état observé des moteurs.

### Body
```json
{}
```

### Réponse
```json
{
  "ok": true,
  "engines": {
    "claude": { "available": true, "reason": null },
    "codex": { "available": true, "reason": null },
    "athos": { "available": true, "reason": "core_runtime" }
  },
  "data_quality": "runtime_observed"
}
```

---

## POST `/api/skills/recommend`

Recommandation prudente, non exécutive.

### Body
```json
{
  "context": {
    "page": "dashboard/automations",
    "task": "frontend QA",
    "phase": "QA"
  }
}
```

### Réponse
- recommandations heuristiques statiques
- `human_approval_required: true`
- `mode: "static_rules"`
- `data_quality: "heuristic"`

---

## Validation

Tests ciblés :

```bash
python -m pytest tests/test_voice_room_endpoints.py tests/test_dashboard_runtime.py -q
```

Tests complets :

```bash
python -m pytest tests/ -q
```
