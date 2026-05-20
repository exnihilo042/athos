# ATHOS — Backlog Codex

**Date** : 2026-05-20 | **Maintenu par** : Claude (architecture)
**Scope** : Tâches réservées au périmètre Codex, non traitées par Claude

Ce fichier est la source de vérité pour les travaux runtime en attente.
Claude ne doit pas implémenter ces items. Codex les reprend à son retour.

---

## STATUT CODEX AU 2026-05-20

| Moteur | État | Cause |
|--------|------|-------|
| chatgpt_plus (Codex CLI) | ⛔ bloqué | usage_limit ChatGPT Plus observé live — reset externe requis |
| claude_code | ✅ disponible | Token actif dans le status live |

---

## P0 — Critique (bloquer le reste)

### CODEX-001 — Retour Codex responder après reset quota

**Priorité** : P0
**Statut** : Dépendance externe — encore bloqué au check live Codex 2026-05-20

**Contexte** :
Le responder Codex (chatgpt_plus) est bloqué depuis 2026-05-19 à cause du dépassement de quota ChatGPT Plus. Le système fonctionne en dégradé sur claude_code uniquement pour la Room.

**État vérifié Codex 2026-05-20** :
- `/api/conversation { action:"runtime" }` retourne `responders.actors.codex.available=false`.
- `last_problem.kind=usage_limit`.
- Claude est `available=true`.
- Aucun test de symbiose réel Claude+Codex n'est possible tant que ce blocage externe persiste.

**Fichiers concernés** :
- `core/room_responders.py` — logique de sélection du responder
- `core/athos_router.py` — détection de disponibilité
- `memory/athos_projects.mem` — mise à jour du statut

**Critères d'acceptation** :
- [ ] `responders.actors.codex.available = true` dans `/api/observability`
- [ ] Room auto-respond fonctionne avec les deux engines (claude + codex)
- [ ] Test Room : envoyer un message "travaillez" → les deux répondent
- [ ] Mettre à jour athos_projects.mem : `codex_responder=available`

---

### CODEX-002 — session_writer.py E2E fiable

**Priorité** : P0
**Statut** : ✅ Livré côté runtime Codex — dépend encore de l'appel explicite en fin de session

**Contexte** :
`write_session()` dans `memory_manager.py` n'est jamais appelé par Codex CLI. La fonction existe, le stop hook Claude Code existe et tourne, mais la chaîne est cassée côté Codex : Codex ne signale pas la fin de session au HUB avant de quitter.

**Solution frontend déjà prête** :
- `/api/memory/note` ajouté à `voice/server.py` (2026-05-20) — endpoint POST qui appelle `write_session(note)`
- Les interfaces TypeScript sont dans `dashboard/lib/types.ts` : `SessionNote`, `SessionNoteResponse`

**Flux livré** :
À la fin de chaque session Codex CLI, appeler :
```bash
scripts/codex_session_note.sh '§session:YYYY-MM-DD|engine=codex|result=...|tasks=...'
```

**Fichiers concernés** :
- `core/memory_manager.py` — `write_session()` (existe, non appelé)
- `core/session_writer.py` — `run()` qui lit `session_notes.mem` (existe)
- `voice/server.py` — `/api/memory/note` (OK)
- `scripts/codex_session_note.sh` — helper Codex avec auth et fallback local
- `tests/test_voice_room_endpoints.py` — endpoint vide/valide testé

**Critères d'acceptation** :
- [x] Après une session Codex, `temp/session_notes.mem` reçoit les notes si le HUB est offline.
- [x] `/api/memory/note` répond `{"ok": true}` à un POST test.
- [x] Payload vide refusé en 400.
- [ ] Le comportement “Codex CLI appelle automatiquement le helper au stop” reste dépendant du runtime externe Codex.

---

## P1 — Important (prochaine session Codex)

### CODEX-003 — SSE backend seed event fiable

**Priorité** : P1
**Statut** : ✅ Validé et couvert par test backend Codex

**Historique du problème** :
La route `POST /api/events` dans `voice/server.py` appelait `observability.get_status()` (ligne ~1332) — fonction inexistante dans `core/observability.py`. L'exception était silencieusement avalée, rendant le seed event SSE vide.

**Correction appliquée** (voice/server.py, commit en attente) :
```python
# AVANT (cassé) :
import observability as _obs
_sse_write("status", _obs.get_status())

# APRÈS (corrigé) :
s = _router.status()
_sse_write("status", {
    **s,
    "session": session_kernel.status(),
    "capability_graph": capability_graph.compact_summary(available_engines=_router.available()),
})
```

**Vérification côté frontend** :
Le proxy SSE Next.js `/api/athos-events` transmet maintenant 2273 bytes à la connexion (vérifié par curl 2026-05-20). Le `TopBar` et le `LiveFeed` reçoivent l'event `status` immédiatement.

**Ce que Codex doit valider** :
- [x] Test backend : `POST /api/events` émet immédiatement `event: status`.
- [x] Le seed contient `session` et `capability_graph`.
- [x] Aucun appel mort à `observability.get_status()`.
- [ ] Test navigateur TopBar/LiveFeed reste dans le scope UI Claude.

**Fichiers concernés** :
- `voice/server.py:1329-1335` — seed event SSE (corrigé)
- `dashboard/app/api/athos-events/route.ts` — proxy (OK)
- `dashboard/components/LiveFeed.tsx` — consommateur (OK)
- `dashboard/components/DashboardShell.tsx` — TopBar SSE (OK)

---

### CODEX-004 — Task queue UI controls (pause / retry / cancel / resume)

**Priorité** : P1
**Statut** : ✅ Backend livré et durci

**Contexte** :
`core/task_queue.py` existe. Le lifecycle `/api/tasks` est opérationnel : `create|get|list|start|pause|resume|retry|cancel|complete|block|sweep_stale`.

La page Automations affiche déjà un état simplifié de la boucle autonome. Les **boutons** pause/retry/cancel/resume ne sont pas implémentés car ils nécessitent une logique de mutation backend sécurisée.

**Transitions documentées** :
- `queued → running|paused|blocked|cancelled`
- `running → completed|blocked|paused|cancelled`
- `paused → queued|blocked|cancelled`
- `blocked → queued|cancelled`
- `completed|cancelled` sont terminaux.

**Frontend déjà prêt** :
```tsx
// dashboard/lib/types.ts — interfaces disponibles
export interface TaskCardProps {
  task: Task;
  onCancel?: (id: string) => void;
  onRetry?: (id: string) => void;
  onPause?: (id: string) => void;
}
```
Une fois le backend validé, Claude peut implémenter les boutons en un seul composant `TaskActions.tsx`.

**Critères d'acceptation** :
- [x] `POST /api/tasks { action: "cancel", task_id }` → tâche en statut `cancelled`
- [x] `POST /api/tasks { action: "retry", task_id }` → tâche relancée si non terminale
- [x] Tests unitaires pour transitions et transitions illégales
- [x] Retour `{ ok: true, task: {...} }` sur succès

---

### CODEX-005 — Reprise automatique des tâches bloquées

**Priorité** : P1
**Statut** : ✅ Socle conservateur implémenté

**Contexte** :
Quand Codex CLI est interrompu (crash, quota, réseau), les tâches `running` restent bloquées indéfiniment. Il n'y a pas de mécanisme de timeout ou de relance automatique.

**Livré** :
- `ATHOS_TASK_STALE_AFTER_SECONDS` défaut `600`.
- `task_queue.sweep_stale()` passe les tâches `running` trop anciennes en `blocked`.
- `blocked_reason=stale_timeout`.
- Pas de retry aveugle.
- Exposé via `/api/tasks { action:"sweep_stale" }` et via `summary()`.

**Fichiers concernés** :
- `core/task_queue.py` — logique principale
- `config.py` — ajouter `ATHOS_TASK_TIMEOUT_MINUTES`

**Critères d'acceptation** :
- [x] Tâche `running` depuis > 10min → passage en `blocked`.
- [x] Log dans session_kernel via `record_action("task_queue","stale_timeout",...)`.
- [x] Observable dans `/api/tasks` et `task_queue.summary()`.

---

### CODEX-006 — Rapports : endpoint /api/report fiable

**Priorité** : P1
**Statut** : ✅ Vérifié et stabilisé backend

**Contexte** :
La page `dashboard/reports/page.tsx` appelle `/api/report { type: "daily" }`. Cet endpoint doit retourner `{ brief, date, sections: [{ title, content }] }`. Non vérifié depuis la mise en place du dashboard.

**Ce que Codex doit valider** :
- [x] `POST /api/report { type: "daily" }` → retourne un rapport structuré.
- [x] Rapport inclut session, task queue, responders, failover.
- [ ] Affichage page dashboard reste validation UI Claude.

**Fichiers concernés** :
- `voice/server.py` — route `/api/report`
- `core/session_compactor.py` — source probable du brief

---

## P2 — Futur (après stabilisation P0/P1)

### CODEX-007 — Autonomous loop controls

**Priorité** : P2
**Statut** : ✅ Backend alias livré, UI reste Claude

**Contexte** :
`core/autonomous_loop.py` existe. La page Automations affiche l'état. Les contrôles `start_loop`, `stop_loop` existent dans le module mais ne sont pas exposés proprement dans une API frontend-friendly avec feedback temps réel.

**Livré** :
- `/api/autonomous_loop` est alias de `/api/loop`.
- `status|start|stop|events` supportés.
- `stop` idempotent testé.
- `start` conserve la garde explicite `allow_autonomous=true` ou env `ATHOS_AUTONOMOUS_LOOP_ENABLED=true`.

**Frontend attendu (Claude après Codex)** :
Boutons Start/Stop dans la page Automations avec feedback SSE temps réel.

---

### CODEX-008 — Finances : endpoint /api/finances

**Priorité** : P2
**Statut** : Non implémenté — données MOCK côté dashboard

**Contexte** :
La page `/dashboard/finances` affiche des données mock (MOCK_CA_MONTH, MOCK_VENTES_NETTES, etc.). Ces données doivent venir d'une source réelle.

**Candidates** :
- Stripe API (abonnements, payments)
- Shopify Admin API (orders, revenue)
- Fichier CSV / Google Sheets

**Ce que Codex doit faire** :
1. Décider de la source de données avec Clément
2. Implémenter l'endpoint `/api/finances` dans `voice/server.py`
3. Retourner le schéma défini dans `dashboard/lib/types.ts` : `FinancesSummary`, `RevenueDataPoint`, `ProjectRevenue`

---

### CODEX-009 — SEO Analytics : endpoint /api/seo

**Priorité** : P2
**Statut** : Non implémenté — données MOCK côté dashboard

**Contexte** :
La page `/dashboard/seo` affiche des données mock. Sources attendues : Google Search Console API, PageSpeed Insights API.

**Schéma frontend prêt** dans `dashboard/lib/types.ts` : `SeoSite`, `CoreWebVital`, `SeoPosition`.

**Ce que Codex doit faire** :
1. Intégration GSC API (nécessite OAuth + credentials)
2. Endpoint `/api/seo` dans `voice/server.py`
3. Cache local (les données GSC ne changent pas toutes les heures)

---

## Notes d'architecture importantes

### SSE — Connexions multiples

Le dashboard ouvre jusqu'à 2 connexions SSE vers le HUB (TopBar + LiveFeed ou Room). Chaque connexion occupe un thread dans `ThreadingHTTPServer`. Acceptable pour 1 utilisateur. Si plusieurs onglets ouverts simultanément → N×2 threads. Pas de problème à court terme.

### Mémoire — write_session() sans appelant

`memory_manager.write_session()` est défini mais sans appelant actif côté Codex. La solution `/api/memory/note` (POST) est en place. Codex doit l'appeler explicitement avant exit.

### Token sécurité

`ATHOS_ACCESS_TOKEN` n'est jamais transmis au client Next.js. Il passe uniquement via `/api/athos-proxy` (server-side) et `/api/athos-events` (server-side). Ne jamais le placer dans `NEXT_PUBLIC_*`.
