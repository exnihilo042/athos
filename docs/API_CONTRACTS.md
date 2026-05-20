# ATHOS — Contrats API

**Version** : 0.8 | **Date** : 2026-05-20
**Base URL** : `http://localhost:7474`
**Auth** : `Authorization: Bearer $ATHOS_ACCESS_TOKEN` (toutes les routes)

---

## Conventions

- Toutes les routes ATHOS HUB sont en **POST** (sauf SSE `/api/events`)
- Content-Type : `application/json`
- Réponse : JSON sauf SSE
- Erreur auth : `{"error": "unauthorized", "auth_required": true}`
- Le dashboard utilise `/api/athos-proxy` comme relai sécurisé

---

## GET /api/athos-events *(Next.js proxy)*

**Statut** : RÉEL

Proxy SSE Next.js → ATHOS HUB `/api/events`.

**Réponse** : `text/event-stream`

```
event: status
data: { engine, degraded, available, budget, spend_policy, session, capability_graph }

event: session_event
data: { id, ts, type, engine, t, ... }

event: heartbeat
data: { ts, server: "athos" }

event: error
data: { error: string }
```

---

## POST /api/status

**Statut** : RÉEL

```json
{
  "engine": "chatgpt_plus",
  "degraded": false,
  "available": ["chatgpt_plus", "claude_code"],
  "budget": 0.0212,
  "spend_policy": { "mode": "zero_paid_api", "room_auto_respond": true, ... },
  "session": { "events": 20, "exchanges": 2, "actions": 6, ... },
  "capability_graph": { "summary": { "nodes": 72, "edges": 132, "austere_mode_ready": true } }
}
```

---

## POST /api/observability

**Statut** : RÉEL

```json
{
  "timestamp": "ISO8601",
  "git": { "branch": "main", "head": "7a1a330", "dirty": [] },
  "server_runtime": { "pid": 94565, "uptime_seconds": 2993 },
  "ports": [ { "command": "...", "pid": 0, "name": "TCP *:7474 (LISTEN)" } ],
  "failover": [ { "ts": "ISO8601", "label": "claude_code → chatgpt_plus", "result": "..." } ],
  "memory": { "ok": true, "missing": [], "canonical_files": [...] },
  "summary": { "listening_ports": 10, "failover_events": 4, "memory_missing": 0 }
}
```

---

## POST /api/capability_graph

**Statut** : RÉEL

```json
{
  "nodes": [
    {
      "id": "string",
      "kind": "engine|memory|capability|...",
      "label": "string",
      "status": "active|planned|missing|...",
      "offline": true,
      "risk": "low|medium|high",
      "cost": "free|low|medium|high",
      "tags": []
    }
  ],
  "principle": "string",
  "summary": {
    "nodes": 72, "edges": 132,
    "available_nodes": 39, "offline_ready_nodes": 51,
    "interconnection_score": 1.0, "austere_mode_ready": true
  }
}
```

---

## POST /api/conversation

**Statut** : RÉEL

**Body** :
```json
{ "action": "get", "limit": 60 }
{ "action": "clear" }
{ "action": "get", "task_id": "room-xxx", "limit": 30 }
```

**Réponse (get)** :
```json
{
  "thread": [
    { "id": "uuid", "ts": "ISO8601", "actor": "clement|claude|codex|athos",
      "type": "message|action|result|error|report|checkpoint",
      "content": "string", "task_id": "string" }
  ],
  "summary": { "total": 42 }
}
```

---

## POST /api/message

**Statut** : RÉEL

**Body** :
```json
{
  "actor": "clement",
  "content": "string",
  "type": "message",
  "task_id": "room-1716210000000"
}
```

**Réponse** :
```json
{
  "ok": true,
  "auto_work": { "scheduled": true, "reason": "string", "entry_id": "uuid" },
  "auto_response": { "scheduled": false }
}
```

---

## POST /api/projects

**Statut** : RÉEL — parsé depuis `athos_projects.mem`

```json
{
  "projects": [
    {
      "name": "placerr",
      "status": "active",
      "priority": "1",
      "stack": "Next.js(web/)+Pixi.js",
      "local": "cd ~/Sites/placerr/web && npm run dev → localhost:3000",
      "state": "6_design_variants_v1-v6_à_choisir",
      "next": "Clément_choisit_variante"
    }
  ]
}
```

**Limite** : Pour un même projet, seule la dernière valeur de chaque champ répété est conservée.

---

## POST /api/settings

**Statut** : RÉEL

```json
{
  "spend_policy": { "mode": "zero_paid_api", "room_auto_respond": true, ... },
  "security_policy": { "bind_host": "127.0.0.1", "port": 7474, "token_configured": true, ... },
  "engine_order": "chatgpt_plus,claude_code,anthropic_api",
  "env": { "ATHOS_ACCESS_TOKEN": "***", "NEXT_PUBLIC_ATHOS_BASE_URL": "http://localhost:7474" }
}
```

---

## POST /api/tasks

**Statut** : RÉEL (core/task_queue.py, scope Codex)

```json
{
  "action": "list|create|get|start|pause|resume|retry|cancel|complete|block|sweep_stale"
}
```

Réponse `list` :
```json
{
  "tasks": [ { "id": "uuid", "task_id": "...", "title": "...", "status": "queued|running|paused|blocked|completed|cancelled", "priority": 5 } ],
  "summary": { "total": 0, "active": 0, "counts": { "queued": 0, "running": 0, "blocked": 0 }, "stale_after_seconds": 600 }
}
```

Transitions runtime :
- `queued → running|paused|blocked|cancelled`
- `running → completed|blocked|paused|cancelled`
- `paused → queued|blocked|cancelled`
- `blocked → queued|cancelled`
- `completed|cancelled` sont terminaux.

---

## POST /api/memory/note

**Statut** : RÉEL — ajouté 2026-05-20 pour session_writer E2E

```json
{ "note": "§session:...|event=..." }
```

Réponse :
```json
{ "ok": true, "written": 42 }
```

**Usage** : Permet à Codex CLI d'écrire dans `session_notes.mem` avant la fin de session.

Helper Codex :
```bash
scripts/codex_session_note.sh '§session:2026-05-20|engine=codex|result=...'
```

---

## POST /api/events *(HUB direct)*

**Statut** : RÉEL — accès via proxy Next.js recommandé

```
HTTP/1.0 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
```

Envoie immédiatement un `event: status` seed, puis tail du kernel JSONL (1s poll), heartbeat 30s.

---

## POST /api/report

**Statut** : RÉEL — double usage

1. Report attach protocol :
```json
{ "attach_id": "...", "engine": "codex", "summary": "...", "status": "completed" }
```

2. Rapport dashboard :
```json
{ "type": "daily" }
```

Réponse dashboard :
```json
{
  "ok": true,
  "type": "daily",
  "date": "YYYY-MM-DD",
  "brief": "Rapport daily ATHOS — ...",
  "sections": [
    { "title": "Session", "content": "...", "data": {} },
    { "title": "Task queue", "content": "...", "data": {} },
    { "title": "Responders", "content": "...", "data": {} },
    { "title": "Failover", "content": "...", "data": {} }
  ]
}
```

---

## POST /api/autonomous_loop

**Statut** : RÉEL — alias backend de `/api/loop`

```json
{ "action": "status|start|stop|events" }
```

`stop` est idempotent. `start` exige `allow_autonomous=true` ou `ATHOS_AUTONOMOUS_LOOP_ENABLED=true`.

---

## POST /api/loop *(alias /api/autonomous_loop)*

**Statut** : RÉEL

```json
{ "action": "status" }
```

Réponse :
```json
{
  "running": false,
  "iterations": 42,
  "idle_ticks": 3,
  "last_event": { "type": "tick", "ts": "ISO8601", "data": {} },
  "events": [ { "type": "tick|failover|skill|...", "ts": "ISO8601", "data": {} } ],
  "policy": {
    "env_enabled": false,
    "default_tick": 60,
    "skill_mutation_enabled": false
  }
}
```

---

## POST /api/skills

**Statut** : RÉEL

```json
{}
```

Réponse :
```json
{
  "skills": [
    { "name": "web_search", "description": "...", "installed": true, "offline": false }
  ]
}
```

---

## Routes non encore implémentées (scope Codex)

| Route | Description | Interface TypeScript | Priorité |
|-------|-------------|----------------------|----------|
| /api/finances | CA, commandes, marge | `FinancesSummary`, `ProjectRevenue` | P2 |
| /api/seo | Positions, CWV, trafic | `SeoSite`, `SeoPosition` | P2 |
| /api/performance | Lighthouse batch, latences | `PerformancePayload` | P1 |
| /api/crm | Clients, leads, pipeline | `CrmPayload`, `CrmClient` | P2 |
| /api/commandes | Shopify orders | `CommandesPayload`, `Order` | P2 |

Toutes les interfaces TypeScript sont définies dans `dashboard/lib/types.ts`.
