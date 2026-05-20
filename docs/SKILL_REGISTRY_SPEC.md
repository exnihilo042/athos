# ATHOS — Skill Registry Specification

**Version** : 1.0 | **Date** : 2026-05-20 | **Périmètre** : P3 — Intégration future

---

## 1. Vue d'ensemble

Le Skill Registry est le catalogue opératoire d'ATHOS. Il documente les 47 skills Claude disponibles via gstack, leur maturity level, leurs phases de cycle de vie, et leur intégration future dans l'orchestration ATHOS.

**Source de vérité** : `dashboard/lib/skill-registry.ts`
**Page dashboard** : `/dashboard/skills`
**Statut actuel** : données statiques locales — orchestration ATHOS P3

---

## 2. Structure de données

### 2.1 Types fondamentaux

```typescript
type SkillCategory =
  | "ui-design"          // Design, UI/UX, composants
  | "browser-testing"    // Navigateur, QA, benchmark
  | "code-quality"       // Review, investigation, santé
  | "planning"           // Planification, architecture
  | "ship-deploy"        // Déploiement, CI/CD
  | "documentation"      // Docs, releases, retros
  | "context-memory"     // Sauvegarde, restauration contexte
  | "scraping"           // Extraction web, skillification
  | "business-experts"   // Shopify, SEO, domaines métier
  | "gstack-agents"      // Orchestration agents, gbrain
  | "utilities";         // Outils généraux

type SkillMaturity =
  | "available_now"             // Disponible et utilisé
  | "strategic"                 // Planifié mais non automatisé
  | "future_athos_integration"; // Intégration ATHOS prévue P3+

type LifecyclePhase =
  | "planning" | "design" | "implementation"
  | "review" | "qa" | "ship" | "monitoring" | "memory";

type UsageLevel =
  | "operator" | "product" | "engineering"
  | "qa" | "strategy" | "automation";

type AthoAgent =
  | "product" | "design" | "engineering" | "qa"
  | "release" | "memory" | "security" | "seo"
  | "shopify" | "athos_core";
```

### 2.2 Interface Skill

```typescript
interface Skill {
  id: string;                    // identifiant unique kebab-case
  name: string;                  // nom lisible
  slash: string;                 // commande /slash
  categories: SkillCategory[];   // multi-catégorie possible
  description: string;           // description courte
  usage_levels: UsageLevel[];
  lifecycle_phases: LifecyclePhase[];
  recommended_for: string[];     // contextes recommandés (strings)
  agents: AthoAgent[];           // agents ATHOS associés
  maturity: SkillMaturity;
  athos_recommendation: string;  // conseil ATHOS opérateur
  athos_integration: boolean;    // intégration ATHOS directe prévue
}
```

---

## 3. Inventaire — 47 skills, 11 catégories

### A. UI Design (5 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| UI/UX Pro Max | /ui-ux-pro-max | available_now |
| Design Review | /design-review | available_now |
| Emil Design Engineer | /emil-design-eng | strategic |
| Framer Motion Animator | /framer-motion-animator | strategic |
| Agent Elements | /agent-elements | strategic |

### B. Browser Testing (9 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Browse | /browse | available_now |
| Open gstack Browser | /open-gstack-browser | available_now |
| Connect Chrome | /connect-chrome | available_now |
| Setup Browser Cookies | /setup-browser-cookies | available_now |
| QA | /qa | available_now |
| QA Only | /qa-only | available_now |
| Canary | /canary | strategic |
| Benchmark | /benchmark | strategic |
| Benchmark Models | /benchmark-models | strategic |

### C. Code Quality (5 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Review | /review | available_now |
| Investigate | /investigate | available_now |
| Health | /health | available_now |
| CSO | /cso | strategic |
| DevEx Review | /devex-review | strategic |

### D. Planning (7 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Plan Engineering Review | /plan-eng-review | available_now |
| Plan CEO Review | /plan-ceo-review | available_now |
| Plan Design Review | /plan-design-review | available_now |
| Plan DevEx Review | /plan-devex-review | strategic |
| Autoplan | /autoplan | available_now |
| Plan Tune | /plan-tune | strategic |
| Office Hours | /office-hours | available_now |

### E. Ship & Deploy (4 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Ship | /ship | available_now |
| Land and Deploy | /land-and-deploy | available_now |
| Setup Deploy | /setup-deploy | strategic |
| Landing Report | /landing-report | strategic |

### F. Documentation (4 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Document Generate | /document-generate | available_now |
| Document Release | /document-release | available_now |
| Retro | /retro | strategic |
| Learn | /learn | strategic |

### G. Context & Memory (2 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Context Save | /context-save | available_now |
| Context Restore | /context-restore | available_now |

### H. Scraping (2 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Scrape | /scrape | available_now |
| Skillify | /skillify | future_athos_integration |

### I. Business Experts (2 skills)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Shopify Expert | /shopify-expert | available_now |
| SEO Expert | /seo-expert | available_now |

### J. gstack Agents (6 skills + agent-elements partagé)
| Skill | Slash | Maturity |
|-------|-------|----------|
| gstack | /gstack | available_now |
| gstack Upgrade | /gstack-upgrade | available_now |
| Setup gbrain | /setup-gbrain | strategic |
| Sync gbrain | /sync-gbrain | strategic |
| Pair Agent | /pair-agent | future_athos_integration |
| Codex | /codex | available_now |

### K. Utilities (1 skill)
| Skill | Slash | Maturity |
|-------|-------|----------|
| Make PDF | /make-pdf | strategic |

---

## 4. Matrice Agents × Skills

10 agents ATHOS définis dans `ATHO_AGENTS`:

| Agent | Couleur | Rôle principal | Skills associés |
|-------|---------|----------------|-----------------|
| product | accent | Vision produit | plan-ceo-review, plan-eng-review, autoplan, office-hours |
| design | blue | Design système | ui-ux-pro-max, design-review, plan-design-review |
| engineering | green | Code et architecture | review, investigate, ship, land-and-deploy |
| qa | yellow | Tests et validation | qa, qa-only, canary, benchmark, browse |
| release | accent | Déploiement | ship, land-and-deploy, setup-deploy, landing-report |
| memory | muted | Contexte | context-save, context-restore, skillify |
| security | red | Sécurité | cso, health, review |
| seo | green | Référencement | seo-expert, scrape |
| shopify | accent | E-commerce | shopify-expert |
| athos_core | blue | Orchestration | gstack, codex, pair-agent, setup-gbrain |

---

## 5. Moteur de recommandation — 14 workflows

| Déclencheur | Skill recommandé |
|-------------|-----------------|
| Nouvelle page ou composant UI | /ui-ux-pro-max |
| Révision design en cours | /design-review ou /plan-design-review |
| Bug signalé | /investigate |
| PR ou review de code | /review |
| Planification architecture | /plan-eng-review |
| QA feature | /qa ou /qa-only |
| Déploiement | /ship ou /land-and-deploy |
| Documentation | /document-generate |
| SEO audit | /seo-expert |
| E-commerce Shopify | /shopify-expert |
| Contexte long → sauvegarder | /context-save |
| Reprendre session | /context-restore |
| Scraping ou extraction | /scrape |
| Orchestration agents | /pair-agent ou /codex |

---

## 6. Intégration ATHOS — Roadmap P3

### Scope actuel (dashboard v8)
- Catalogue statique complet dans `skill-registry.ts`
- Page `/dashboard/skills` : filtres, cards, matrix, recommendation engine
- Composants UI : `SkillCategoryBadge`, `SkillMaturityBadge`
- Intégration légère : Hub (ModuleCard + ProductRow), Agents (lien), Automations (lien SectionLabel)

### P3 — Orchestration réelle (scope Codex futur)

```
/api/skills/registry        GET  → liste enrichie avec last_used, call_count
/api/skills/recommend       POST {context, phase, agent} → skill_id[] recommandés
/api/skills/execute         POST {skill_id, params} → déclenche skill via ATHOS_HUB
/api/skills/log             POST {skill_id, result, duration} → historique usage
/api/skills/metrics         GET  → stats usage par skill, agent, phase
```

**Prérequis P3** :
- Integration registry ATHOS (sources réelles par projet)
- Social registry (canaux, automatisations)
- Room multi-IA collaborative avec orchestrateur consensus
- Moteur proactivité watchtower (déclenche skills automatiquement)

### Colonne `athos_integration: true`

Ces skills ont `athos_integration: true` — ils sont en tête de liste pour l'orchestration P3 :
- `/context-save`, `/context-restore` — mémoire session
- `/qa`, `/qa-only` — validation automatique post-déploiement
- `/investigate` — diagnostic automatique sur alerte
- `/ship`, `/land-and-deploy` — pipeline CI/CD automatisé
- `/skillify` — auto-acquisition de nouveaux skills

---

## 7. Règles d'évolution du registre

1. **Ajouter un skill** : ajouter dans `SKILLS[]` dans `skill-registry.ts`, recalculer `SKILL_STATS`
2. **Toujours dédupliquer** : un skill = un enregistrement, `categories[]` multiple si besoin
3. **Ne jamais supprimer** : marquer `maturity: "strategic"` si le skill n'est plus actif
4. **ATHOS_SPEC.md** : mettre à jour la table section 2 pour refléter le total skills
5. **Co-author** : tout commit → `Jerykko/Ex-nihilo <contact@ex-nihilo.agency>`
