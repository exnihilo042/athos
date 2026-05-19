# ATHOS — Intégration multi-moteur Claude ↔ Codex ↔ ATHOS

> Protocole d'unification. Tous les moteurs lisent ce fichier.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   ATHOS HUB :7474                    │
│                                                      │
│  agentmemory :8765 │ 9router :20128 │ gbrain PGLite  │
│  mémoire partagée  │ proxy OpenAI   │ knowledge graph │
└──────────────────────────────────────────────────────┘
         ↑                  ↑                  ↑
    Claude Code           Codex CLI          ATHOS UI
    ~/.claude/skills/   ~/.codex/skills/   localhost:7474
```

---

## Commande universelle — "use ATHOS" / "utilises ATHOS"

Quand Claude ou Codex reçoit cette commande :

1. Lire `~/Sites/athos/ATHOS_ATTACH_PROMPT.md`
2. Appeler `GET http://localhost:7474/api/status`
3. Afficher le **récap initial** :
   - Sites actifs + résultats financiers (CA, conversion, panier moyen)
   - SEO : positions clés, trafic organique, Core Web Vitals
   - Contenus récents + leur performance
4. Afficher dans le **tab "Sites"** de l'UI ATHOS

---

## Skills partagés — inventaire croisé

### Claude voit
```
~/.claude/skills/    → gstack (~51 skills), agent-elements, emil-design-eng,
                        framer-motion-animator, seo-expert, shopify-expert,
                        ui-ux-pro-max
```

### Codex voit
```
~/.codex/skills/     → ~89 skills dont :
  agent-skills/      → 23 skills Addy Osmani (symlinks)
  athos-architects/  → 5 personas experts
  ui-references/     → repos UI locaux
  shopify-references/ → Dawn, Polaris, awesome-shopify
  + tous les skills Shopify, Figma, Deploy, Notion, SEO, UI/UX...
```

### Accès croisé
- Claude lit les skills Codex : `cat ~/.codex/skills/<name>/SKILL.md`
- Codex lit les skills Claude : `cat ~/.claude/skills/<name>/SKILL.md`
- ATHOS agrège les deux via `/api/skills`

### Règle de mise à jour

Après toute modification durable, le moteur doit :

1. écrire agentmemory si `:8765` est en ligne ;
2. écrire une note offline dans `~/Sites/athos/memory/session_YYYYMMDD.mem` si agentmemory est offline ;
3. reporter l'action dans ATHOS Room via `/api/message` ou `athos_report` ;
4. mettre à jour `memory/athos_projects.mem` si un statut/prochain checkpoint change ;
5. pour ATHOS, synchroniser aussi le Drive `Mon Drive/CLAUDE AI/` et GitHub `exnihilo042/athos`, sauf blocage explicite ou demande contraire ;
6. ne jamais stage/push les caches, venv, DB locales, PID, logs temporaires ou secrets.

### Cloisonnement strict ATHOS / projets clients

- Une modification ATHOS ne doit jamais créer de fichier dans un projet client, export thème, dossier Shopify, `Downloads` ou repo non ATHOS.
- Cibles autorisées pour ATHOS :
  - `/Users/clem/Sites/athos`
  - `/Users/clem/Library/CloudStorage/GoogleDrive-contact@ex-nihilo.agency/Mon Drive/CLAUDE AI/`
  - `https://github.com/exnihilo042/athos`
- Pour ATHOS, utiliser des chemins absolus avec `apply_patch`. Les chemins relatifs ne sont autorisés que si le `cwd` est confirmé comme `/Users/clem/Sites/athos`.
- Si un artefact ATHOS est créé ailleurs : le supprimer, scanner les projets clients, reporter l'incident dans Room/mémoire, puis committer la correction de protocole.

---

## Mémoire partagée — agentmemory

Endpoint : `http://localhost:8765`

**Écrire** (tâche importante / fin de session) :
```bash
curl -s -X POST http://localhost:8765/memories \
  -H "Content-Type: application/json" \
  -d '{"category":"athos","document":"[résumé]"}'
```

**Lire** (début de session / recherche) :
```bash
curl -s http://localhost:8765/memories/search \
  -H "Content-Type: application/json" \
  -d '{"query":"projets en cours","n_results":5}'
```

**Catégories** : `athos` | `shopify` | `seo` | `client:<nom>` | `code` | `session`

---

## 9router — proxy OpenAI-compatible

Dashboard : `http://localhost:20128/dashboard`
**Action utilisateur requise** : configurer les providers API dans le dashboard.

Pointer les outils sur `localhost:20128` pour router via 9router :
- Économise 20-40% de tokens (RTK compression)
- Fallback automatique subscription → cheap → free

---

## gbrain — knowledge graph local

```bash
cd ~/Sites/athos/skills/references/gbrain
bun run src/cli.ts query "quels projets sont actifs ?"
bun run src/cli.ts import ~/Sites/athos/memory/
```

---

## Boot ATHOS — services lancés automatiquement

| Service | Port | Démarrage |
|---------|------|-----------|
| ATHOS server | 7474 | `cd ~/Sites/athos && source venv/bin/activate && python voice/server.py` |
| agentmemory | 8765 | Automatique au boot ATHOS |
| 9router | 20128 | Automatique au boot ATHOS |
| weekly update | — | 1×/semaine au boot |

---

## Tabs ATHOS UI — à implémenter

- **Sites** : dashboard financier + SEO par domaine (résultat "use ATHOS")
- **Skills** : inventaire Claude + Codex + statut actif
- **Mémoire** : interface de recherche agentmemory + Drive
- **9router** : iframe → `localhost:20128/dashboard`
- **gbrain** : query interface knowledge graph
