/**
 * ATHOS — Skill Registry
 *
 * Catalogue structuré des 47 skills Claude disponibles (agent-elements apparaît
 * dans deux catégories : ui-design et gstack-agents).
 * Source canonique : ~/.claude/skills/
 *
 * Utilisé par : /dashboard/skills, Hub, Agents, Automations
 * Scope Codex futur : /api/skills/registry, /api/skills/recommend
 */

// ── Types ──────────────────────────────────────────────────────────────────

export type SkillCategory =
  | "ui-design"
  | "browser-testing"
  | "code-quality"
  | "planning"
  | "ship-deploy"
  | "documentation"
  | "context-memory"
  | "scraping"
  | "business-experts"
  | "gstack-agents"
  | "utilities";

export type SkillMaturity =
  | "available_now"
  | "strategic"
  | "future_athos_integration";

export type LifecyclePhase =
  | "planning"
  | "design"
  | "implementation"
  | "review"
  | "qa"
  | "ship"
  | "monitoring"
  | "memory";

export type UsageLevel =
  | "operator"
  | "product"
  | "engineering"
  | "qa"
  | "strategy"
  | "automation";

export type AthoAgent =
  | "product"
  | "design"
  | "engineering"
  | "qa"
  | "release"
  | "memory"
  | "security"
  | "seo"
  | "shopify"
  | "athos_core";

export interface Skill {
  id: string;
  name: string;
  slash: string;
  categories: SkillCategory[];
  description: string;
  usage_levels: UsageLevel[];
  lifecycle_phases: LifecyclePhase[];
  recommended_for: string[];
  agents: AthoAgent[];
  maturity: SkillMaturity;
  athos_recommendation: string;
  athos_integration: boolean;
}

// ── Category metadata ──────────────────────────────────────────────────────

export interface CategoryMeta {
  label: string;
  icon: string;
  color: string;
}

export const SKILL_CATEGORIES: Record<SkillCategory, CategoryMeta> = {
  "ui-design":        { label: "UI / Design / Frontend",   icon: "◉",  color: "var(--accent)" },
  "browser-testing":  { label: "Browser & Tests",           icon: "◳",  color: "var(--green)" },
  "code-quality":     { label: "Qualité code & Review",     icon: "◲",  color: "var(--blue)" },
  "planning":         { label: "Planning & Architecture",   icon: "◱",  color: "var(--accent-2)" },
  "ship-deploy":      { label: "Ship & Déploiement",        icon: "⟳",  color: "var(--green)" },
  "documentation":    { label: "Documentation",             icon: "◫",  color: "var(--muted)" },
  "context-memory":   { label: "Contexte & Mémoire",        icon: "◈",  color: "var(--accent)" },
  "scraping":         { label: "Scraping & Données",        icon: "◼",  color: "var(--blue)" },
  "business-experts": { label: "Experts métier",            icon: "◾",  color: "var(--yellow)" },
  "gstack-agents":    { label: "GStack & Agents IA",        icon: "⬡",  color: "var(--accent-2)" },
  "utilities":        { label: "Utilitaires",               icon: "◻",  color: "var(--muted)" },
};

// ── Agent metadata ─────────────────────────────────────────────────────────

export interface AgentMeta {
  label: string;
  description: string;
  color: string;
  primary_categories: SkillCategory[];
}

export const ATHO_AGENTS: Record<AthoAgent, AgentMeta> = {
  product:      { label: "Product Agent",      description: "Stratégie, roadmap, décisions produit",         color: "var(--accent)",   primary_categories: ["planning", "documentation"] },
  design:       { label: "Design Agent",       description: "UI/UX, design system, polish",                  color: "var(--accent-2)", primary_categories: ["ui-design"] },
  engineering:  { label: "Engineering Agent",  description: "Code, architecture, implémentation",             color: "var(--blue)",     primary_categories: ["code-quality", "ship-deploy"] },
  qa:           { label: "QA Agent",           description: "Tests, audit qualité, validation",               color: "var(--green)",    primary_categories: ["browser-testing", "code-quality"] },
  release:      { label: "Release Agent",      description: "Ship, déploiement, changelog",                   color: "var(--green)",    primary_categories: ["ship-deploy", "documentation"] },
  memory:       { label: "Memory Agent",       description: "Contexte, mémoire, persistance",                 color: "var(--muted)",    primary_categories: ["context-memory", "documentation"] },
  security:     { label: "Security Agent",     description: "Audit sécurité, OWASP, secrets",                 color: "var(--red)",      primary_categories: ["code-quality"] },
  seo:          { label: "SEO Agent",          description: "Positions, contenu, GSC",                        color: "var(--yellow)",   primary_categories: ["business-experts"] },
  shopify:      { label: "Shopify Agent",      description: "Thèmes Liquid, API Admin, e-commerce",           color: "var(--yellow)",   primary_categories: ["business-experts"] },
  athos_core:   { label: "ATHOS Core",         description: "Orchestrateur central — arbitre et recommande",  color: "var(--accent)",   primary_categories: ["planning", "gstack-agents", "context-memory"] },
};

// ── Skill workflows (Recommendation Engine) ────────────────────────────────

export interface WorkflowTrigger {
  trigger: string;
  skill_id: string;
  when: string;
}

export const SKILL_WORKFLOWS: WorkflowTrigger[] = [
  { trigger: "Avant gros chantier produit",         skill_id: "autoplan",          when: "Avant de commencer une nouvelle feature majeure" },
  { trigger: "Avant implémentation UI",             skill_id: "plan-design-review", when: "Avant d'écrire le premier composant" },
  { trigger: "Après gros chantier frontend",        skill_id: "qa-only",            when: "Avant commit — audit sans modifier" },
  { trigger: "Après correctifs",                    skill_id: "health",             when: "Vérifier l'état global du code après patches" },
  { trigger: "Avant merge de branche",              skill_id: "review",             when: "Systématiquement — review diff complet" },
  { trigger: "Avant release",                       skill_id: "cso",                when: "Audit sécurité avant exposition publique" },
  { trigger: "Après ship en production",            skill_id: "canary",             when: "Surveillance post-déploiement" },
  { trigger: "Fin de session de travail",           skill_id: "context-save",       when: "Toujours — sans exception" },
  { trigger: "Idée nouvelle produit",               skill_id: "office-hours",       when: "Avant de coder — valider l'idée" },
  { trigger: "Bug ou erreur inexpliqué",            skill_id: "investigate",        when: "Dès apparition d'un problème non trivial" },
  { trigger: "Avant décision architecture",         skill_id: "plan-eng-review",    when: "En amont du code — éviter la dette" },
  { trigger: "Après optimisation performance",      skill_id: "benchmark",          when: "Mesurer le gain réel" },
  { trigger: "Après déploiement",                   skill_id: "document-release",   when: "Mettre docs et changelog à jour" },
  { trigger: "Nouvelle feature Shopify",            skill_id: "shopify-expert",     when: "Pour tout développement Liquid ou API Admin" },
];

// ── Skills data ────────────────────────────────────────────────────────────

export const SKILLS: Skill[] = [
  // A. UI / Design / Frontend
  {
    id: "ui-ux-pro-max",
    name: "UI/UX Pro Max",
    slash: "/ui-ux-pro-max",
    categories: ["ui-design"],
    description: "Design & implementation brain augmenté — librairies de styles, 161 palettes, typographies, patterns UX, chart decisions, stacks.",
    usage_levels: ["product", "engineering", "operator"],
    lifecycle_phases: ["design", "implementation"],
    recommended_for: ["Conception interface", "Choix typographie / palette", "Architecture UX"],
    agents: ["design", "product"],
    maturity: "available_now",
    athos_recommendation: "Avant toute décision de design ou création de composant",
    athos_integration: true,
  },
  {
    id: "design-review",
    name: "Design Review",
    slash: "/design-review",
    categories: ["ui-design"],
    description: "Review design sur screenshots — spacing, hiérarchie visuelle, polish premium, responsive.",
    usage_levels: ["product", "qa"],
    lifecycle_phases: ["design", "review", "qa"],
    recommended_for: ["Revue visuelle UI", "Avant release frontend", "Polish premium"],
    agents: ["design", "qa"],
    maturity: "available_now",
    athos_recommendation: "Avant chaque release UI ou ajout de page",
    athos_integration: true,
  },
  {
    id: "emil-design-eng",
    name: "Emil Design Eng",
    slash: "/emil-design-eng",
    categories: ["ui-design"],
    description: "Designer-turned-engineer — finition haut niveau, comparatifs avant/après, polish produit premium.",
    usage_levels: ["product", "engineering"],
    lifecycle_phases: ["design", "implementation", "review"],
    recommended_for: ["Finition UI premium", "Comparatifs avant/après", "Polish final"],
    agents: ["design", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Après implémentation d'un composant complexe — polish final",
    athos_integration: false,
  },
  {
    id: "framer-motion-animator",
    name: "Framer Motion Animator",
    slash: "/framer-motion-animator",
    categories: ["ui-design"],
    description: "Animations et micro-interactions Framer Motion — transitions fluides, spring physics, motion design.",
    usage_levels: ["engineering"],
    lifecycle_phases: ["design", "implementation"],
    recommended_for: ["Animations UI", "Micro-interactions", "Transitions de page"],
    agents: ["design", "engineering"],
    maturity: "strategic",
    athos_recommendation: "Lors de l'ajout d'animations à une interface ATHOS",
    athos_integration: false,
  },
  {
    id: "agent-elements",
    name: "Agent Elements",
    slash: "/agent-elements",
    categories: ["ui-design", "gstack-agents"],
    description: "Composants UI spécialisés pour interfaces d'agents IA — patterns agentiques, Room UI, War Room.",
    usage_levels: ["product", "engineering"],
    lifecycle_phases: ["design", "implementation"],
    recommended_for: ["Interfaces multi-agents", "Dashboard IA", "Room / War Room UI"],
    agents: ["design", "engineering", "athos_core"],
    maturity: "strategic",
    athos_recommendation: "Lors de la conception de composants pour la Room ou les agents ATHOS",
    athos_integration: true,
  },

  // B. Browser & Tests
  {
    id: "browse",
    name: "Browse",
    slash: "/browse",
    categories: ["browser-testing"],
    description: "Browser headless pour naviguer, interagir, vérifier et capturer des pages web.",
    usage_levels: ["qa", "engineering", "automation"],
    lifecycle_phases: ["qa", "monitoring"],
    recommended_for: ["Vérification UI", "Tests navigation", "Capture screenshots"],
    agents: ["qa", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Après modification UI pour vérification visuelle automatique",
    athos_integration: true,
  },
  {
    id: "open-gstack-browser",
    name: "Open GStack Browser",
    slash: "/open-gstack-browser",
    categories: ["browser-testing"],
    description: "Chromium visible contrôlé par IA — interactions complexes, tests authentifiés, debug visuel.",
    usage_levels: ["qa", "engineering"],
    lifecycle_phases: ["qa"],
    recommended_for: ["Tests authentifiés", "Interactions complexes", "Debug visuel"],
    agents: ["qa"],
    maturity: "available_now",
    athos_recommendation: "Pour tests nécessitant une session authentifiée",
    athos_integration: false,
  },
  {
    id: "connect-chrome",
    name: "Connect Chrome",
    slash: "/connect-chrome",
    categories: ["browser-testing"],
    description: "Alias navigateur visible — connexion à Chrome existant pour contrôle IA.",
    usage_levels: ["qa", "engineering"],
    lifecycle_phases: ["qa"],
    recommended_for: ["Connexion Chrome en cours", "Debug interactif", "Session active"],
    agents: ["qa"],
    maturity: "available_now",
    athos_recommendation: "Quand Chrome est déjà ouvert et doit être contrôlé par IA",
    athos_integration: false,
  },
  {
    id: "setup-browser-cookies",
    name: "Setup Browser Cookies",
    slash: "/setup-browser-cookies",
    categories: ["browser-testing"],
    description: "Configuration cookies authentifiés pour tests avec sessions persistantes (Shopify, CRM, etc.).",
    usage_levels: ["qa", "engineering"],
    lifecycle_phases: ["qa"],
    recommended_for: ["Tests authentifiés", "Sessions e-commerce", "Zones privées"],
    agents: ["qa", "shopify"],
    maturity: "strategic",
    athos_recommendation: "Avant tests nécessitant connexion (Shopify admin, CRM, etc.)",
    athos_integration: false,
  },
  {
    id: "qa",
    name: "QA",
    slash: "/qa",
    categories: ["browser-testing"],
    description: "QA complet avec corrections automatiques — audit + fixes inline + revalidation.",
    usage_levels: ["qa", "engineering"],
    lifecycle_phases: ["qa", "review"],
    recommended_for: ["Gros chantier frontend terminé", "Avant merge", "Validation complète"],
    agents: ["qa", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Après un gros chantier frontend avant commit",
    athos_integration: true,
  },
  {
    id: "qa-only",
    name: "QA Only",
    slash: "/qa-only",
    categories: ["browser-testing"],
    description: "Audit QA sans modification — rapport structuré des problèmes détectés.",
    usage_levels: ["qa"],
    lifecycle_phases: ["qa", "review"],
    recommended_for: ["Audit rapide", "Rapport QA indépendant", "Validation sans modification"],
    agents: ["qa"],
    maturity: "available_now",
    athos_recommendation: "Après livraison frontend pour audit indépendant sans risque",
    athos_integration: true,
  },
  {
    id: "canary",
    name: "Canary",
    slash: "/canary",
    categories: ["browser-testing"],
    description: "Monitoring post-déploiement — surveillance continue après mise en production.",
    usage_levels: ["qa", "automation"],
    lifecycle_phases: ["monitoring", "ship"],
    recommended_for: ["Post-déploiement", "Surveillance production", "Régression monitoring"],
    agents: ["qa", "release"],
    maturity: "strategic",
    athos_recommendation: "Après chaque déploiement en production — surveillance automatique",
    athos_integration: true,
  },
  {
    id: "benchmark",
    name: "Benchmark",
    slash: "/benchmark",
    categories: ["browser-testing"],
    description: "Performance web — mesure Lighthouse, Core Web Vitals, comparaisons avant/après.",
    usage_levels: ["engineering", "qa"],
    lifecycle_phases: ["qa", "monitoring"],
    recommended_for: ["Après optimisation perf", "Comparaison avant/après", "Audit Lighthouse"],
    agents: ["engineering", "qa"],
    maturity: "available_now",
    athos_recommendation: "Après optimisation de performance pour mesurer le gain réel",
    athos_integration: true,
  },
  {
    id: "benchmark-models",
    name: "Benchmark Models",
    slash: "/benchmark-models",
    categories: ["browser-testing"],
    description: "Comparaison Claude / GPT / Codex / Gemini — qualité, vitesse, coût sur une tâche.",
    usage_levels: ["strategy", "engineering"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Choix de moteur IA", "Comparaison qualité", "Optimisation budget IA"],
    agents: ["athos_core", "engineering"],
    maturity: "strategic",
    athos_recommendation: "Avant de choisir un moteur IA pour un workflow critique ATHOS",
    athos_integration: true,
  },

  // C. Qualité code & Review
  {
    id: "review",
    name: "Review",
    slash: "/review",
    categories: ["code-quality"],
    description: "Review pré-merge — diff complet, qualité, sécurité, conventions, commentaires inline.",
    usage_levels: ["engineering", "qa"],
    lifecycle_phases: ["review", "ship"],
    recommended_for: ["Avant merge de branche", "Review PR", "Validation diff"],
    agents: ["engineering", "qa", "release"],
    maturity: "available_now",
    athos_recommendation: "Systématiquement avant tout merge de branche",
    athos_integration: true,
  },
  {
    id: "investigate",
    name: "Investigate",
    slash: "/investigate",
    categories: ["code-quality"],
    description: "Debugging systématique — diagnostic root cause, erreurs inexpliquées, incidents.",
    usage_levels: ["engineering"],
    lifecycle_phases: ["implementation", "monitoring"],
    recommended_for: ["Bug inexpliqué", "Incident production", "Root cause analysis"],
    agents: ["engineering", "athos_core"],
    maturity: "available_now",
    athos_recommendation: "Sur tout problème dont la cause n'est pas immédiatement évidente",
    athos_integration: true,
  },
  {
    id: "health",
    name: "Health",
    slash: "/health",
    categories: ["code-quality"],
    description: "Dashboard qualité code — dette technique, couverture tests, conventions, métriques.",
    usage_levels: ["engineering", "strategy"],
    lifecycle_phases: ["review", "monitoring"],
    recommended_for: ["Audit dette technique", "Qualité globale", "Après correctifs"],
    agents: ["engineering", "qa"],
    maturity: "available_now",
    athos_recommendation: "Après un correctif pour vérifier l'état global du code",
    athos_integration: true,
  },
  {
    id: "cso",
    name: "CSO",
    slash: "/cso",
    categories: ["code-quality"],
    description: "Audit Chief Security Officer — vulnérabilités OWASP, dépendances, secrets, surfaces d'attaque.",
    usage_levels: ["strategy", "engineering"],
    lifecycle_phases: ["review", "ship"],
    recommended_for: ["Audit sécurité", "Avant release publique", "Détection secrets"],
    agents: ["security", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Avant toute release exposée publiquement — non négociable",
    athos_integration: true,
  },
  {
    id: "devex-review",
    name: "DevEx Review",
    slash: "/devex-review",
    categories: ["code-quality"],
    description: "Audit developer experience — setup, onboarding, frictions tooling, DX score.",
    usage_levels: ["engineering", "product"],
    lifecycle_phases: ["review"],
    recommended_for: ["Audit DX", "Setup développeur", "Frictions tooling"],
    agents: ["engineering", "product"],
    maturity: "available_now",
    athos_recommendation: "Lors de la revue d'un nouveau projet ou outil",
    athos_integration: false,
  },

  // D. Planning & Architecture
  {
    id: "plan-eng-review",
    name: "Plan Eng Review",
    slash: "/plan-eng-review",
    categories: ["planning"],
    description: "Review architecture engineering manager — découpage, dette technique, risques, scalabilité.",
    usage_levels: ["engineering", "strategy"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Avant décision architecture", "Découpage technique", "Risques système"],
    agents: ["engineering", "athos_core"],
    maturity: "available_now",
    athos_recommendation: "Avant toute décision d'architecture — en amont du code",
    athos_integration: true,
  },
  {
    id: "plan-ceo-review",
    name: "Plan CEO Review",
    slash: "/plan-ceo-review",
    categories: ["planning"],
    description: "Review CEO / fondateur — impact business, priorisation, retour investissement.",
    usage_levels: ["strategy", "product"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Décision business", "Priorisation produit", "Impact utilisateur"],
    agents: ["product", "athos_core"],
    maturity: "available_now",
    athos_recommendation: "Avant de lancer un chantier avec impact business significatif",
    athos_integration: true,
  },
  {
    id: "plan-design-review",
    name: "Plan Design Review",
    slash: "/plan-design-review",
    categories: ["planning"],
    description: "Review plan design — architecture UX, parcours utilisateur, cohérence design system.",
    usage_levels: ["product", "strategy"],
    lifecycle_phases: ["planning", "design"],
    recommended_for: ["Avant implémentation UI", "Architecture UX", "Design system"],
    agents: ["design", "product"],
    maturity: "available_now",
    athos_recommendation: "Avant implémentation d'une nouvelle page ou fonctionnalité",
    athos_integration: true,
  },
  {
    id: "plan-devex-review",
    name: "Plan DevEx Review",
    slash: "/plan-devex-review",
    categories: ["planning"],
    description: "Review plan developer experience — setup, tooling, onboarding, workflow optimisation.",
    usage_levels: ["engineering", "strategy"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Audit setup dev", "Onboarding tooling", "Workflow optimisation"],
    agents: ["engineering"],
    maturity: "available_now",
    athos_recommendation: "Lors de la mise en place d'un nouveau workflow ou outil",
    athos_integration: false,
  },
  {
    id: "autoplan",
    name: "AutoPlan",
    slash: "/autoplan",
    categories: ["planning"],
    description: "Lance tous les reviews et arbitre automatiquement — CEO + Eng + Design + DevEx reviews.",
    usage_levels: ["strategy", "product", "engineering"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Avant gros chantier", "Décision multi-dimension", "Arbitrage automatique"],
    agents: ["athos_core", "product", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Avant tout chantier nécessitant validation multi-dimension",
    athos_integration: true,
  },
  {
    id: "plan-tune",
    name: "Plan Tune",
    slash: "/plan-tune",
    categories: ["planning"],
    description: "Ajuste la sensibilité des prompts et questionnements dans les skills de planning.",
    usage_levels: ["operator"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Calibrage prompts", "Ajustement sensibilité review", "Configuration"],
    agents: ["athos_core"],
    maturity: "strategic",
    athos_recommendation: "Pour calibrer le comportement des skills de planning d'ATHOS",
    athos_integration: false,
  },
  {
    id: "office-hours",
    name: "Office Hours",
    slash: "/office-hours",
    categories: ["planning"],
    description: "Mode YC Office Hours — feedback direct sur idée ou produit, conseil fondateur exigeant.",
    usage_levels: ["strategy", "product"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Nouvelle idée produit", "Validation concept", "Conseil stratégique"],
    agents: ["product", "athos_core"],
    maturity: "available_now",
    athos_recommendation: "Avant de coder une nouvelle fonctionnalité — valider l'idée d'abord",
    athos_integration: true,
  },

  // E. Ship & Déploiement
  {
    id: "ship",
    name: "Ship",
    slash: "/ship",
    categories: ["ship-deploy"],
    description: "Merge branche, tests, review diff, version, changelog, push, PR — pipeline ship complet.",
    usage_levels: ["engineering", "operator"],
    lifecycle_phases: ["ship", "review"],
    recommended_for: ["Release feature", "Merge branche", "Changelog + PR"],
    agents: ["release", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Quand une feature est prête à merger et livrer",
    athos_integration: true,
  },
  {
    id: "land-and-deploy",
    name: "Land & Deploy",
    slash: "/land-and-deploy",
    categories: ["ship-deploy"],
    description: "Merge PR + CI + vérification canary — pipeline déploiement production complet.",
    usage_levels: ["engineering", "automation"],
    lifecycle_phases: ["ship", "monitoring"],
    recommended_for: ["Déploiement production", "CI/CD", "Post-ship canary"],
    agents: ["release", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Après validation QA quand la PR est prête en prod",
    athos_integration: true,
  },
  {
    id: "setup-deploy",
    name: "Setup Deploy",
    slash: "/setup-deploy",
    categories: ["ship-deploy"],
    description: "Configuration déploiement — CI/CD, environments, secrets, workflows GitHub Actions.",
    usage_levels: ["engineering"],
    lifecycle_phases: ["planning", "ship"],
    recommended_for: ["Nouveau projet", "Configuration CI/CD", "Setup environments"],
    agents: ["engineering", "release"],
    maturity: "available_now",
    athos_recommendation: "En début de projet pour configurer le pipeline de déploiement",
    athos_integration: false,
  },
  {
    id: "landing-report",
    name: "Landing Report",
    slash: "/landing-report",
    categories: ["ship-deploy"],
    description: "État queue de ship — vision globale des branches en attente de merge ou déploiement.",
    usage_levels: ["operator", "strategy"],
    lifecycle_phases: ["ship", "review"],
    recommended_for: ["Vue pipeline ship", "Gestion branches", "Priorisation releases"],
    agents: ["release", "athos_core"],
    maturity: "strategic",
    athos_recommendation: "Pour avoir une vue globale des releases en attente",
    athos_integration: false,
  },

  // F. Documentation
  {
    id: "document-generate",
    name: "Document Generate",
    slash: "/document-generate",
    categories: ["documentation"],
    description: "Génération docs Diataxis — tutorials, how-to guides, références, explications structurées.",
    usage_levels: ["product", "engineering"],
    lifecycle_phases: ["review", "ship"],
    recommended_for: ["Nouvelle fonctionnalité", "API docs", "Guide utilisateur"],
    agents: ["memory", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Après livraison d'une feature pour documenter proprement",
    athos_integration: false,
  },
  {
    id: "document-release",
    name: "Document Release",
    slash: "/document-release",
    categories: ["documentation"],
    description: "Mise à jour docs après ship — CHANGELOG, release notes, migration guides.",
    usage_levels: ["engineering", "product"],
    lifecycle_phases: ["ship"],
    recommended_for: ["Post-release", "CHANGELOG", "Notes de version"],
    agents: ["release", "memory"],
    maturity: "available_now",
    athos_recommendation: "Immédiatement après chaque ship pour tenir les docs à jour",
    athos_integration: false,
  },
  {
    id: "retro",
    name: "Retro",
    slash: "/retro",
    categories: ["documentation"],
    description: "Rétrospective engineering — ce qui a marché, ce qui n'a pas, améliorations process.",
    usage_levels: ["strategy", "engineering"],
    lifecycle_phases: ["memory"],
    recommended_for: ["Fin de sprint", "Post-incident", "Apprentissage collectif"],
    agents: ["athos_core", "engineering"],
    maturity: "available_now",
    athos_recommendation: "En fin de session ou sprint pour capitaliser les apprentissages",
    athos_integration: true,
  },
  {
    id: "learn",
    name: "Learn",
    slash: "/learn",
    categories: ["documentation"],
    description: "Apprentissages persistants — capture et stockage des learnings dans gstack.",
    usage_levels: ["operator", "automation"],
    lifecycle_phases: ["memory"],
    recommended_for: ["Capture apprentissage", "Learnings gstack", "Persistance contexte"],
    agents: ["memory", "athos_core"],
    maturity: "strategic",
    athos_recommendation: "Quand une décision ou découverte mérite d'être mémorisée",
    athos_integration: true,
  },

  // G. Contexte & Mémoire
  {
    id: "context-save",
    name: "Context Save",
    slash: "/context-save",
    categories: ["context-memory"],
    description: "Sauvegarde contexte session — état HEAD, décisions, fichiers modifiés, suite à faire.",
    usage_levels: ["operator", "automation"],
    lifecycle_phases: ["memory"],
    recommended_for: ["Fin de session", "Avant changement de contexte", "Point de sauvegarde"],
    agents: ["memory", "athos_core"],
    maturity: "available_now",
    athos_recommendation: "Systématiquement en fin de toute session de travail — obligatoire",
    athos_integration: true,
  },
  {
    id: "context-restore",
    name: "Context Restore",
    slash: "/context-restore",
    categories: ["context-memory"],
    description: "Restaure contexte session — reprend là où la session précédente s'est arrêtée.",
    usage_levels: ["operator"],
    lifecycle_phases: ["memory", "planning"],
    recommended_for: ["Reprise session", "Changement de machine", "Continuité contexte"],
    agents: ["memory", "athos_core"],
    maturity: "available_now",
    athos_recommendation: "En début de session pour retrouver le contexte exact précédent",
    athos_integration: true,
  },

  // H. Scraping & Données
  {
    id: "scrape",
    name: "Scrape",
    slash: "/scrape",
    categories: ["scraping"],
    description: "Extraction web — scraping structuré de données depuis pages web.",
    usage_levels: ["automation", "engineering"],
    lifecycle_phases: ["implementation"],
    recommended_for: ["Collecte données", "Monitoring concurrent", "Data extraction"],
    agents: ["athos_core", "seo"],
    maturity: "available_now",
    athos_recommendation: "Pour collecter des données web structurées dans un workflow",
    athos_integration: true,
  },
  {
    id: "skillify",
    name: "Skillify",
    slash: "/skillify",
    categories: ["scraping"],
    description: "Codifie un flow scrape réussi — transforme un scrape ad-hoc en skill réutilisable.",
    usage_levels: ["engineering", "automation"],
    lifecycle_phases: ["implementation"],
    recommended_for: ["Réutilisation scrape", "Capitalisation workflow", "Automatisation"],
    agents: ["athos_core", "engineering"],
    maturity: "strategic",
    athos_recommendation: "Après un scrape réussi pour le rendre réutilisable",
    athos_integration: true,
  },

  // I. Experts métier (agent-elements already counted in A)
  {
    id: "shopify-expert",
    name: "Shopify Expert",
    slash: "/shopify-expert",
    categories: ["business-experts"],
    description: "Expertise Shopify — thèmes Liquid, API Admin, custom apps, e-commerce patterns.",
    usage_levels: ["engineering", "product"],
    lifecycle_phases: ["planning", "implementation", "review"],
    recommended_for: ["Développement Shopify", "Thème Liquid", "API Admin"],
    agents: ["shopify", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Pour tout développement sur Shopify (Rouge Pivoine, Olivia, etc.)",
    athos_integration: true,
  },
  {
    id: "seo-expert",
    name: "SEO Expert",
    slash: "/seo-expert",
    categories: ["business-experts"],
    description: "Expertise SEO — stratégie organique, audit technique, content, positions GSC.",
    usage_levels: ["product", "strategy"],
    lifecycle_phases: ["planning", "monitoring"],
    recommended_for: ["Audit SEO", "Stratégie contenu", "Optimisation positions"],
    agents: ["seo", "product"],
    maturity: "available_now",
    athos_recommendation: "Pour décisions SEO ou analyse des positions organiques",
    athos_integration: true,
  },

  // J. GStack & Agents IA
  {
    id: "gstack",
    name: "GStack",
    slash: "/gstack",
    categories: ["gstack-agents"],
    description: "Préambule / setup — initialise le contexte gstack pour la session en cours.",
    usage_levels: ["operator"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Initialisation session", "Setup gstack", "Contexte initial"],
    agents: ["athos_core"],
    maturity: "available_now",
    athos_recommendation: "En début de session pour initialiser l'environnement gstack",
    athos_integration: false,
  },
  {
    id: "gstack-upgrade",
    name: "GStack Upgrade",
    slash: "/gstack-upgrade",
    categories: ["gstack-agents"],
    description: "Upgrade GStack — mise à jour vers la dernière version des skills gstack.",
    usage_levels: ["operator"],
    lifecycle_phases: ["planning"],
    recommended_for: ["Mise à jour GStack", "Nouvelles fonctionnalités", "Maintenance"],
    agents: ["athos_core"],
    maturity: "available_now",
    athos_recommendation: "Quand une nouvelle version de GStack est signalée au démarrage",
    athos_integration: false,
  },
  {
    id: "setup-gbrain",
    name: "Setup GBrain",
    slash: "/setup-gbrain",
    categories: ["gstack-agents"],
    description: "Mémoire vectorielle — configure GBrain pour recherche sémantique dans le codebase.",
    usage_levels: ["engineering", "operator"],
    lifecycle_phases: ["planning", "memory"],
    recommended_for: ["Recherche sémantique", "Navigation codebase", "Mémoire vectorielle"],
    agents: ["memory", "engineering"],
    maturity: "strategic",
    athos_recommendation: "Pour indexer un nouveau repo dans GBrain — recherche sémantique",
    athos_integration: true,
  },
  {
    id: "sync-gbrain",
    name: "Sync GBrain",
    slash: "/sync-gbrain",
    categories: ["gstack-agents"],
    description: "Ré-indexe repo dans GBrain — maintient la mémoire vectorielle à jour après changements.",
    usage_levels: ["operator", "automation"],
    lifecycle_phases: ["memory"],
    recommended_for: ["Synchronisation mémoire", "Après changements importants", "Index à jour"],
    agents: ["memory", "athos_core"],
    maturity: "strategic",
    athos_recommendation: "Après un gros chantier pour maintenir GBrain synchronisé",
    athos_integration: true,
  },
  {
    id: "pair-agent",
    name: "Pair Agent",
    slash: "/pair-agent",
    categories: ["gstack-agents"],
    description: "Paire agent IA distant avec navigateur local — contrôle navigateur depuis agent.",
    usage_levels: ["engineering", "automation"],
    lifecycle_phases: ["implementation", "qa"],
    recommended_for: ["Agent distant", "Contrôle navigateur", "Automation complexe"],
    agents: ["athos_core", "engineering"],
    maturity: "strategic",
    athos_recommendation: "Pour orchestrer un agent IA qui contrôle un navigateur local",
    athos_integration: true,
  },
  {
    id: "codex",
    name: "Codex",
    slash: "/codex",
    categories: ["gstack-agents"],
    description: "Wrapper Codex CLI — lancer Codex, passer des tâches, monitorer l'exécution backend.",
    usage_levels: ["engineering", "automation"],
    lifecycle_phases: ["implementation"],
    recommended_for: ["Tâches backend", "Codex CLI", "Exécution runtime"],
    agents: ["athos_core", "engineering"],
    maturity: "available_now",
    athos_recommendation: "Pour déléguer une tâche backend ou runtime à Codex",
    athos_integration: true,
  },

  // K. Utilitaires
  {
    id: "make-pdf",
    name: "Make PDF",
    slash: "/make-pdf",
    categories: ["utilities"],
    description: "Export markdown en PDF publication-quality — rapports, specs, documents clients.",
    usage_levels: ["product", "operator"],
    lifecycle_phases: ["ship"],
    recommended_for: ["Rapports clients", "Specs produit", "Documents publication"],
    agents: ["memory", "product"],
    maturity: "strategic",
    athos_recommendation: "Pour exporter un rapport ou spec en PDF partageable avec clients",
    athos_integration: false,
  },
];

// ── Computed helpers ───────────────────────────────────────────────────────

export const SKILL_STATS = {
  total: SKILLS.length,
  categories: Object.keys(SKILL_CATEGORIES).length,
  available_now: SKILLS.filter((s) => s.maturity === "available_now").length,
  strategic: SKILLS.filter((s) => s.maturity === "strategic").length,
  future_athos: SKILLS.filter((s) => s.maturity === "future_athos_integration").length,
  athos_integration: SKILLS.filter((s) => s.athos_integration).length,
} as const;

export function getSkillById(id: string): Skill | undefined {
  return SKILLS.find((s) => s.id === id);
}

export function getSkillsByCategory(category: SkillCategory): Skill[] {
  return SKILLS.filter((s) => s.categories.includes(category));
}

export function getSkillsByAgent(agent: AthoAgent): Skill[] {
  return SKILLS.filter((s) => s.agents.includes(agent));
}
