# ATHOS — Backlog Codex

**Date** : 2026-05-20 | **Maintenu par** : Claude (architecture)
**Scope** : Tâches réservées au périmètre Codex, non traitées par Claude

Ce fichier est la source de vérité pour les travaux runtime en attente.
Claude ne doit pas implémenter ces items. Codex les reprend à son retour.

---

## STATUT CODEX AU 2026-05-20

| Moteur | État | Cause |
|--------|------|-------|
| chatgpt_plus (Codex CLI) | ⛔ bloqué | usage_limit ChatGPT Plus — reset en attente |
| claude_code | ✅ disponible | Token actif |

---

## P0 — Critique (bloquer le reste)

### CODEX-001 — Retour Codex responder après reset quota

**Priorité** : P0
**Statut** : En attente reset ChatGPT Plus

**Contexte** :
Le responder Codex (chatgpt_plus) est bloqué depuis 2026-05-19 à cause du dépassement de quota ChatGPT Plus. Le système fonctionne en dégradé sur claude_code uniquement pour la Room.

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
**Statut** : Diagnostic complet, correction partielle

**Contexte** :
`write_session()` dans `memory_manager.py` n'est jamais appelé par Codex CLI. La fonction existe, le stop hook Claude Code existe et tourne, mais la chaîne est cassée côté Codex : Codex ne signale pas la fin de session au HUB avant de quitter.

**Solution frontend déjà prête** :
- `/api/memory/note` ajouté à `voice/server.py` (2026-05-20) — endpoint POST qui appelle `write_session(note)`
- Les interfaces TypeScript sont dans `dashboard/lib/types.ts` : `SessionNote`, `SessionNoteResponse`

**Ce que Codex doit faire** :
À la fin de chaque session Codex CLI, appeler :
```bash
curl -s -X POST http://localhost:7474/api/memory/note \
  -H "Authorization: Bearer $ATHOS_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"note": "§session:YYYY-MM-DD|engine=codex|result=...|tasks=..."}'
```

**Fichiers concernés** :
- `core/memory_manager.py` — `write_session()` (existe, non appelé)
- `core/session_writer.py` — `run()` qui lit `session_notes.mem` (existe)
- `voice/server.py:1300+` — `/api/memory/note` (ajouté, OK)

**Critères d'acceptation** :
- [ ] Après une session Codex, `memory/temp/session_notes.mem` contient des données
- [ ] Le stop hook Claude Code (`session_writer.py`) lit et route correctement
- [ ] `/api/memory/note` répond `{"ok": true}` à un POST test

---

## P1 — Important (prochaine session Codex)

### CODEX-003 — SSE backend seed event fiable

**Priorité** : P1
**Statut** : ✅ Corrigé en session Claude 2026-05-20 — À VALIDER par Codex

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
- [ ] Test E2E : ouvrir le dashboard → TopBar affiche le moteur dans < 1s
- [ ] Test E2E : Room SSE déclenche un refresh du fil à chaque kernel event
- [ ] Confirmer que le seed event survit à un redémarrage du serveur

**Fichiers concernés** :
- `voice/server.py:1329-1335` — seed event SSE (corrigé)
- `dashboard/app/api/athos-events/route.ts` — proxy (OK)
- `dashboard/components/LiveFeed.tsx` — consommateur (OK)
- `dashboard/components/DashboardShell.tsx` — TopBar SSE (OK)

---

### CODEX-004 — Task queue UI controls (pause / retry / cancel / resume)

**Priorité** : P1
**Statut** : Frontend prêt, backend à compléter

**Contexte** :
`core/task_queue.py` existe avec 194 tests. Le CRUD de base est opérationnel (`/api/tasks`). Les interfaces TypeScript sont définies dans `dashboard/lib/types.ts` (`Task`, `TaskQueue`, `TaskCardProps`, `TaskQueueViewProps`).

La page Automations affiche déjà un état simplifié de la boucle autonome. Les **boutons** pause/retry/cancel/resume ne sont pas implémentés car ils nécessitent une logique de mutation backend sécurisée.

**Ce que Codex doit faire** :
1. Vérifier que `/api/tasks` accepte `{ action: "cancel", task_id: "..." }`, `{ action: "retry", task_id: "..." }`, `{ action: "pause", task_id: "..." }`
2. Implémenter la logique de transition d'état dans `core/task_queue.py`
3. Documenter les états valides et les transitions autorisées

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
- [ ] `POST /api/tasks { action: "cancel", task_id }` → tâche en statut `cancelled`
- [ ] `POST /api/tasks { action: "retry", task_id }` → tâche relancée
- [ ] Test unitaire pour chaque transition
- [ ] Retour `{ ok: true, task: {...} }` sur succès

---

### CODEX-005 — Reprise automatique des tâches bloquées

**Priorité** : P1
**Statut** : Non implémenté

**Contexte** :
Quand Codex CLI est interrompu (crash, quota, réseau), les tâches `running` restent bloquées indéfiniment. Il n'y a pas de mécanisme de timeout ou de relance automatique.

**Ce que Codex doit faire** :
1. Ajouter un watchdog dans `core/task_queue.py` (ou un script séparé)
2. Détecter les tâches `running` depuis plus de N minutes (configurable)
3. Les passer en `failed` avec un message explicite
4. Optionnel : les re-queuer selon une politique configurable

**Fichiers concernés** :
- `core/task_queue.py` — logique principale
- `config.py` — ajouter `ATHOS_TASK_TIMEOUT_MINUTES`

**Critères d'acceptation** :
- [ ] Tâche `running` depuis > 10min → passage automatique en `failed`
- [ ] Log dans session_kernel : `{"type": "task_timeout", "task_id": "..."}`
- [ ] Observable dans `/api/tasks` et dans le dashboard Automations

---

### CODEX-006 — Rapports : endpoint /api/report fiable

**Priorité** : P1
**Statut** : Endpoint existe, comportement non vérifié

**Contexte** :
La page `dashboard/reports/page.tsx` appelle `/api/report { type: "daily" }`. Cet endpoint doit retourner `{ brief, date, sections: [{ title, content }] }`. Non vérifié depuis la mise en place du dashboard.

**Ce que Codex doit valider** :
- [ ] `POST /api/report { type: "daily" }` → retourne un rapport structuré
- [ ] Le rapport inclut au minimum : session summary, failover events, tasks done
- [ ] La page dashboard affiche les sections correctement

**Fichiers concernés** :
- `voice/server.py` — route `/api/report`
- `core/session_compactor.py` — source probable du brief

---

## P2 — Futur (après stabilisation P0/P1)

### CODEX-007 — Autonomous loop controls

**Priorité** : P2
**Statut** : Loop existe, contrôles UI non implémentés

**Contexte** :
`core/autonomous_loop.py` existe. La page Automations affiche l'état. Les contrôles `start_loop`, `stop_loop` existent dans le module mais ne sont pas exposés proprement dans une API frontend-friendly avec feedback temps réel.

**Ce que Codex doit faire** :
1. S'assurer que `/api/autonomous_loop` accepte `{ action: "start" }` et `{ action: "stop" }` de manière idempotente
2. Retourner un état cohérent après chaque action
3. Émettre des events dans session_kernel sur start/stop

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
