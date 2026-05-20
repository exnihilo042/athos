# ATHOS — Règles Agents & Séparation des Responsabilités

**Version** : 0.6 | **Date** : 2026-05-20

---

## 1. Principe fondamental

ATHOS sépare strictement les responsabilités entre moteurs. Cette séparation évite les conflits, les régressions, et garantit que chaque moteur intervient dans son domaine de compétence.

**Règle d'or** : Avant toute modification, identifier si le changement touche le runtime (Codex) ou la présentation (Claude). Si ambiguïté → Codex par défaut pour tout ce qui touche `core/`.

---

## 2. Périmètre Claude (produit, UX, architecture)

### Peut modifier

| Zone | Exemples |
|------|---------|
| `dashboard/app/` | Pages, layouts, routes Next.js |
| `dashboard/components/` | Composants React |
| `dashboard/lib/ui/` | Utilities UI |
| `dashboard/lib/charts/` | Visualisations |
| `dashboard/lib/types.ts` | Interfaces TypeScript |
| `docs/` | Documentation technique |
| `memory/*.mem` | Mise à jour mémoire ATHOS |
| `voice/server.py` | Routes HTTP superficielles (lecture mem, proxy) |

### Ne doit PAS modifier

| Zone | Raison |
|------|--------|
| `core/task_queue.py` | Runtime Codex, logique persistance tâches |
| `core/athos_engine.py` | Orchestration LLM profonde |
| `core/athos_router.py` | Logique failover moteurs |
| `core/room_responders.py` | Responders runtime |
| `core/session_writer.py` | Stop hook système |
| Workers/background jobs | Runtime Codex |
| Logique retry moteur | Runtime Codex |

### Exception : bug critique

Si Claude identifie un bug critique dans une zone Codex (ex : regression test, crash serveur), il peut documenter le bug et la solution proposée dans un TODO structuré, mais **ne doit pas implémenter** sans validation explicite.

---

## 3. Périmètre Codex (runtime, orchestration, tests)

### Peut modifier

| Zone | Exemples |
|------|---------|
| `core/` (tout) | task_queue, athos_engine, session_kernel |
| `voice/server.py` | Routes runtime complexes, workers |
| `tests/` | Suite de tests |
| Scripts bash | restart, sync, launchd |
| `.github/workflows/` | CI/CD |

### Ne doit PAS modifier

| Zone | Raison |
|------|--------|
| `dashboard/` | Périmètre Claude |
| `docs/DESIGN_SYSTEM.md` | Décisions UX Claude |
| Fichiers `.mem` (sans instruction) | Mémoire ATHOS, écriture via write_session() |

---

## 4. Règles de communication inter-moteurs

### Via Room

Clément écrit dans Room. ATHOS achemine vers le bon moteur selon la nature du message :
- Message travail → auto-work (Codex ou Claude selon la tâche)
- Question ponctuelle → auto-respond (Claude prioritaire)
- Coordination → multi-round si configuré

### Via /api/memory/note

Codex peut écrire dans la mémoire session avant de terminer :
```json
POST /api/memory/note
{ "note": "§session:2026-05-20|result=task_done|..." }
```

### Via session_kernel

Tout moteur peut `record_action()` dans le kernel JSONL. Ces events sont broadcastés via SSE.

---

## 5. Règles de mémoire

1. **Format obligatoire** : §-compressé, pipe-séparé, pas de prose
2. **Écriture** : via `memory_manager.write_session()` ou `/api/memory/note`
3. **Lecture** : directe (fichier) ou via `/api/projects`, `/api/settings`
4. **Mise à jour** : à chaque fin de session significative
5. **Jamais** : effacer des entrées sans archivage préalable

---

## 6. Règles de commit

| Règle | Description |
|-------|-------------|
| Jamais sans demande | Ne pas committer sans instruction explicite de Clément |
| Co-author | `Jerykko/Ex-nihilo <contact@ex-nihilo.agency>` toujours |
| Jamais Claude comme auteur primaire | Le co-author est Claude, pas le primary |
| --no-verify interdit | Sauf bug démontré de hook |
| Force push main interdit | Toujours |
| Staging précis | Jamais `git add -A` sans vérification |

---

## 7. Règles de sécurité

| Règle | Détail |
|-------|--------|
| ATHOS_ACCESS_TOKEN | Jamais logué, jamais en clair dans le code, server-side only |
| CORS :7474 | `localhost` uniquement, strict |
| Write roots | Limité à `~/Sites/athos` par défaut |
| API token frontend | Passé via /api/athos-proxy uniquement |
| Endpoints validés | /api/athos-proxy valide `endpoint.startsWith("/api/")` |

---

## 8. Acceptation d'un lot

Avant de marquer un lot comme terminé, vérifier :

- [ ] Build Next.js sans erreur TypeScript
- [ ] Tests backend : `python -m pytest tests/ -q` ≥ 194 passing
- [ ] Pages fonctionnelles en HTTP 200
- [ ] Données MOCK clairement identifiées (MockBanner + commentaires `MOCK_`)
- [ ] Données RÉELLES vérifiées (curl /api/endpoint)
- [ ] Mémoire mise à jour (athos_projects.mem)
- [ ] Docs mises à jour si architecture change
- [ ] Séparation Claude/Codex respectée

---

## 9. Limites connues au 2026-05-20

| Limite | Impact | Résolution |
|--------|--------|-----------|
| session_writer.py non E2E | Mémoire session Codex non persistée | Attente Codex CLI actif |
| Codex responder usage_limit | Room sans réponse Codex | Attente reset ChatGPT Plus |
| Finances sans données réelles | Dashboard mock uniquement | Intégration Stripe/Shopify API |
| SEO sans données réelles | Dashboard mock uniquement | Intégration GSC API |
| Tests dashboard inexistants | Régressions UI non détectées | Playwright E2E à prévoir |
