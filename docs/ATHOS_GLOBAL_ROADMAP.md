# ATHOS — Roadmap Globale

**Version** : 1.0 | **Date** : 2026-05-20 | **Source** : Claude Sonnet 4.6

---

## VISION FONDATRICE — NE PAS OUBLIER

ATHOS n'est pas un dashboard. ATHOS est une trajectoire.

> **ERP IA futuriste · OS de supervision intelligent · Centre de commande multi-IA
> Cockpit multi-projets · Orchestrateur d'agents · Outil business complet
> → JARVIS personnel et professionnel.**

Cette roadmap grave chaque pilier restant à bâtir.
Le dashboard actuel est une **fondation solide**, pas l'achèvement de la vision.

---

## ÉTAT ACTUEL — 2026-05-20

### Ce qui est livré et fonctionnel

| Composant | Statut | Version |
|-----------|--------|---------|
| ATHOS HUB Python :7474 | ✅ RÉEL | Runtime stable |
| Routeur moteurs multi-IA | ✅ RÉEL | chatgpt_plus › claude_code › api › ollama |
| Room multi-IA (REST + auto-work) | ✅ RÉEL | Réponse automatique active |
| Mémoire §-format persistante | ✅ RÉEL | ~/Sites/athos/memory/ |
| Capability graph (72 nœuds) | ✅ RÉEL | Score 1.0, austere mode ready |
| Task queue + boucle autonome | ✅ RÉEL | 201 tests passants |
| Observabilité complète | ✅ RÉEL | /api/observability — failover, ports, mémoire |
| Dashboard Next.js v5 | ✅ LIVRÉ | 19 routes, 0 TS errors |
| SSE live events | ✅ RÉEL | /api/athos-events → /api/events HUB |
| Auth token + CORS strict | ✅ RÉEL | ATHOS_ACCESS_TOKEN, localhost only |
| Pages : Hub, Room, Agents, Alertes | ✅ RÉEL | Données temps réel |
| Pages : Projects, Settings, Automations, Reports | ✅ RÉEL | Données réelles |
| Pages : Finances, SEO, Commandes, CRM, Performance | 🔸 MOCK/MIXTE | Backend à brancher |
| Design system unifié | ✅ LIVRÉ | InsetNotice, PageHeader, EmptyPanel, etc. |
| Project Control Center | 🚧 P2 | Frontend prototype — en cours |

---

## P0 — STABILITÉ SYSTÈME (FAIT OU EN COURS)

**Objectif** : fondation technique inattaquable.

- [x] HUB HTTP ThreadingMixIn — robuste, concurrent
- [x] SSE streaming — /api/events → dashboard live
- [x] Auth ATHOS_ACCESS_TOKEN — CORS strict localhost
- [x] Dashboard 19 routes — 0 erreur TypeScript
- [x] Room multi-IA — envoi, réception, auto-work, auto-respond
- [x] Capability graph réel — 72 nœuds, edges, score
- [x] Task queue — état machine, transitions légales, stale sweep
- [x] Observabilité — failover, ports, launchd, mémoire
- [x] Mémoire persistante §-format — write via session_writer.py
- [x] Design system — composants partagés, tokens CSS, grilles responsives
- [ ] Session writer E2E — dépend Codex CLI actif (usage_limit)
- [ ] Codex responder — bloqué usage_limit, à débloquer

---

## P1 — PILOTAGE OPÉRATEUR RÉEL (ACTIF)

**Objectif** : Clément peut superviser et piloter chaque dimension de son activité depuis ATHOS.

### Dashboard Business — backend à brancher

| Page | Status | Source à connecter | Scope |
|------|--------|-------------------|-------|
| Finances | MIXTE (budget réel / CA mock) | Stripe API ou Shopify Admin | Codex P2 |
| Commandes | MOCK | Shopify Admin API | Codex P2 |
| CRM / Clients | MOCK | /api/crm (parsing mem) | Codex P2 |
| SEO Analytics | MOCK | Google Search Console API | Codex P2 |
| Performance | MIXTE (score réel / Lighthouse mock) | Lighthouse CLI | Codex P1 |

### Room multi-IA — enrichissement

- [ ] Fil de conversation structuré par projet
- [ ] Historique paginé (>60 messages)
- [ ] Recherche dans la Room
- [ ] Tags/labels sur les messages
- [ ] Filtres par acteur, type, date

### Observabilité avancée

- [ ] Graphe de capacités interactif (zoomable, filtrable)
- [ ] Timeline des failovers
- [ ] Budget IA par moteur (tokens, coût, sessions)
- [ ] Health score détaillé par composant

---

## P2 — PROJECT CONTROL CENTER (DÉMARRAGE)

**Objectif** : ATHOS devient un ERP réellement multi-projets.
Chaque projet est une entité pilotable. Les pages SEO, Finances, Commandes, CRM deviennent liées à un projet réel.

### 2.1 — Project Control Center (PCC)

**Frontend prototype démarré cette session.**

- [ ] Page liste projets enrichie (filtres, statut, priorité, vue ERP)
- [ ] Page détail projet — fiche complète (prototype frontend)
- [ ] Wizard création projet — 7 étapes (prototype frontend)
- [ ] Backend persistance projets → Codex scope
- [ ] API /api/projects enrichie (CRUD complet)

### 2.2 — Integration Registry

Pour chaque projet, rattacher :

- [ ] Site web / domaine
- [ ] Repository GitHub
- [ ] Google Drive dossier dédié
- [ ] Shopify store
- [ ] Stripe account
- [ ] Google Search Console property
- [ ] Google Analytics / Plausible
- [ ] CRM entrées
- [ ] Hébergement / VPS
- [ ] Monitoring endpoint
- [ ] Outils internes ATHOS

### 2.3 — Social & Channel Registry

Pour chaque projet :

- [ ] Instagram
- [ ] TikTok
- [ ] LinkedIn
- [ ] X / Twitter
- [ ] Facebook
- [ ] Pinterest
- [ ] YouTube
- [ ] Newsletter (Brevo / Mailchimp)
- [ ] Canaux custom

### 2.4 — Project Agents Registry

Pour chaque projet :

- [ ] Agents IA dédiés (SEO, Dev, Finance, Content, Automation)
- [ ] Rôle, permissions, mémoire dédiée
- [ ] Outils autorisés par agent
- [ ] Degré d'autonomie
- [ ] Budget IA par agent
- [ ] Dernière activité, historique

### 2.5 — Project Goals & KPIs

Métriques à piloter par projet :

- [ ] CA mensuel / annuel
- [ ] Trafic organique
- [ ] Leads générés
- [ ] Commandes
- [ ] Positions SEO (top 3, top 10)
- [ ] Publications contenu
- [ ] Taux de conversion
- [ ] Marge
- [ ] Tickets ouverts / dette technique
- [ ] Score santé projet (composite)

---

## P3 — INTÉGRATIONS BUSINESS RÉELLES

**Objectif** : ATHOS agit vraiment dans les outils, pas seulement les lit.

### Sources de données réelles

- [ ] Shopify Admin API — commandes, produits, clients, inventaire
- [ ] Stripe API — revenus, abonnements, remboursements
- [ ] Google Search Console API — positions, clics, impressions
- [ ] Google PageSpeed Insights — Core Web Vitals réels
- [ ] Google Analytics 4 / Plausible — trafic, conversions
- [ ] GitHub API — commits, PRs, issues, CI status
- [ ] Notion / Airtable / Dolibarr — CRM / ERP

### Actions réelles sur outils (write access)

- [ ] Publier un post social (Instagram, LinkedIn, X)
- [ ] Créer/modifier un produit Shopify
- [ ] Envoyer une newsletter (Brevo/Mailchimp)
- [ ] Créer un ticket GitHub issue
- [ ] Mettre à jour une fiche CRM
- [ ] Envoyer un email transactionnel (Gmail API)
- [ ] Déclencher un workflow automatisé

### Connecteurs moteurs supplémentaires

- [ ] OpenRouter (fallback multi-modèles)
- [ ] Google Gemini / Vertex
- [ ] Grok (xAI)
- [ ] DeepSeek, Mistral, Together, Cerebras
- [ ] LM Studio / llama.cpp local

---

## P4 — AUTONOMIE MULTI-AGENTS ET PROACTIVITÉ

**Objectif** : ATHOS surveille, détecte, recommande et agit sans qu'on lui demande.

### Room multi-IA vraiment collaborative

La Room doit devenir une **war room IA collective** :

- [ ] Plusieurs IA discutent ensemble sur un problème
- [ ] Débats structurés : positions, contre-arguments, consensus
- [ ] Répartition des tâches inter-agents (Claude planifie, Codex exécute)
- [ ] ATHOS arbitre ou synthétise les désaccords
- [ ] Orchestrateur de consensus visible
- [ ] Propositions multiples d'approches comparées
- [ ] Décisions visibles (pas de pensées brutes exposées)
- [ ] Plans visibles, désaccords résumés, justifications synthétiques
- [ ] Mode War Room : focus intensif sur un problème critique
- [ ] Mode Mission Control : supervision globale en temps réel

### Moteur de proactivité

- [ ] Watchtower business — détection d'anomalies business automatique
- [ ] Watchtower SEO — alertes positions perdues, erreurs crawl
- [ ] Watchtower infra — alertes CPU, mémoire, latence, downtime
- [ ] Watchtower commandes — spike ou chute de CA
- [ ] Watchtower social — engagement anormal
- [ ] Recommandation autonome — ATHOS propose sans qu'on demande
- [ ] Alertes prédictives — avant que le problème soit critique
- [ ] Routine nommées — `ATHOS_GROWTH_REVIEW`, `ATHOS_CLIENT_DAILY`, etc.

### Knowledge Graph

- [ ] Graphe de connaissances persistant (projets × clients × outils × événements)
- [ ] Relations entre entités (projet → client → repo → commandes)
- [ ] Inférences automatiques (si repo change → alerte projet lié)
- [ ] Mémoire long terme structurée par entité
- [ ] Résumé contextuel automatique par projet

---

## P5 — JARVIS OMNIPRÉSENT

**Objectif** : ATHOS est présent partout, tout le temps, avec ou sans écran.

### Voice & Présence

- [ ] Assistant vocal local — wake word + STT local gratuit
- [ ] TTS réponse vocale (naturelle, non robotique)
- [ ] Orb ATHOS CORE dans l'UI — présence visuelle permanente
- [ ] Mode voix navigateur — sans application dédiée
- [ ] iPhone PWA stable — accès sécurisé distant complet

### Multi-device & Edge Agents

- [ ] Edge agent Mac — surveillance locale continue
- [ ] Edge agent iPhone — notifications push, actions mobiles
- [ ] Edge agent VPS always-on — présence 24/7 même Mac éteint
- [ ] Edge agent serveur — déploiements automatisés
- [ ] TV / HUD — affichage ambient dashboard
- [ ] HUD AR / lunettes (long terme)

### Gouvernance & Multi-utilisateur

- [ ] Multi-utilisateur — permissions par rôle (admin, viewer, agent)
- [ ] Audit trail complet — toute action tracée, visible, réversible
- [ ] Permissions granulaires — par projet, par outil, par agent
- [ ] API publique sécurisée — pour intégrations tierces
- [ ] Mode client — vue limitée pour partager avec clients

### Modes avancés

- [ ] Mode Mission Control — vue globale temps réel tous projets
- [ ] Mode War Room — focus intensif collaboration IA
- [ ] Mode Austère — fonctionnel offline, sans réseau, sans cloud
- [ ] Mode Reporting — résumé exécutif automatique (daily/weekly)
- [ ] Mode Prédictif — projections CA, trafic, risques

### Vision finale

- [ ] Système prédictif — anticipe les besoins avant formulation
- [ ] Wake word physique — Athos répond sans écran
- [ ] Contrôle Mac avancé — automation système, screenshot, vision
- [ ] Scan réseau défensif — sur réseaux autorisés uniquement
- [ ] Robotique / multi-environnements (très long terme)

---

## ANCRES PERMANENTES

Ces principes ne doivent jamais être perdus :

| Principe | Description |
|----------|-------------|
| Vérité > confort | ATHOS ne flatte pas, corrige les biais, sépare faits/inférences |
| Zéro dépense par défaut | Aucune API payante sans opt-in explicite |
| Austérité locale | Fonctionnel offline, sans cloud, sans capteurs |
| Transparence | Toute action visible, loggée, stoppable |
| Garde-fou Ultron | ATHOS amplifie, ne remplace pas le jugement humain |
| Cloisonnement Claude/Codex | Dashboard/produit = Claude · Runtime/backend = Codex |
| Mémoire canonique | Tout ce qu'ATHOS apprend persiste en §-format |

---

## PROJETS ACTIFS SUIVIS (état 2026-05-20)

| Projet | Priorité | Statut | Prochain |
|--------|----------|--------|----------|
| ATHOS | P0 | building | Project Control Center frontend |
| Placerr | P1 | active | Clément choisit variante design |
| MeetMe | P2 | active | UI/UX responsive (bloqué : .env Supabase) |
| Nearby | P3 | active | Choisir design (v1-v4) |
| Prospection | P4 | active | Envoyer batch J0 (bloqué : SMTP pwd) |
| Rouge Pivoine | P5 | active | Thème draft → push GitHub |
| Olivia | P6 | pending | Push GitHub branch |

---

## CE QUI MANQUE ENCORE POUR ATHOS = JARVIS RÉEL

*Cette section est une ancre anti-oubli. Le dashboard actuel est une fondation, pas l'aboutissement.*

1. **Project Control Center** — ERP multi-projets pilotable
2. **Integration Registry** — outils connectés par projet
3. **Social Channel Registry** — réseaux suivis par projet
4. **Room multi-IA active** — vraie collaboration inter-agents
5. **Orchestrateur de consensus** — arbitrage ATHOS entre IA
6. **Moteur de proactivité** — watchtowers, alertes prédictives
7. **Memory graph** — knowledge graph structuré par entité
8. **Voice layer** — STT/TTS local, wake word
9. **Device/edge layer** — Mac, iPhone, VPS agents
10. **Alertes prédictives** — avant que le problème soit critique
11. **Action réelle sur outils** — écriture dans Shopify, GitHub, GSC
12. **Mode Mission Control** — supervision globale temps réel
13. **Mode War Room** — collaboration IA intensive
14. **Orb ATHOS CORE** — présence visuelle permanente dans l'UI
15. **Assistant vocal** — wake word + réponse naturelle
16. **Gouvernance permissions** — multi-user, audit trail, roles
17. **Système prédictif** — anticipe avant formulation
