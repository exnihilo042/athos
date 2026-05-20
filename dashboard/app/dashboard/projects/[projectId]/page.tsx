import { PageHeader, Badge, InsetNotice, IntegrationBadge, SocialChannelPill, ProjectSection } from "@/components/ui";
import Link from "next/link";

// ── Prototype data — clearly identified ───────────────────────────────────────
// Source future : POST /api/projects/detail — voir docs/PROJECT_CONTROL_CENTER_SPEC.md
// Scope Codex P2

interface Integration {
  tool: string;
  status: "connected" | "configured" | "error" | "not_configured";
  ref?: string;
  detail?: string;
}

interface SocialChannel {
  platform: string;
  handle?: string;
  configured: boolean;
  followers?: number;
  last_post?: string;
}

interface ProjectAgent {
  role: string;
  engine: string;
  autonomy: string;
  last_activity?: string;
  status: "active" | "idle" | "blocked";
}

interface ProjectGoal {
  label: string;
  target: number;
  current: number;
  unit: string;
  trend?: "up" | "down" | "stable";
}

interface ProjectAlert {
  severity: "error" | "warn" | "info";
  message: string;
  action?: string;
}

interface ProjectTask {
  label: string;
  status: "done" | "pending" | "blocked";
}

interface ProjectData {
  id: string;
  name: string;
  type: string;
  status: string;
  priority: number;
  description: string;
  domains: string[];
  repo?: string;
  drive?: string;
  health_score: number;
  integrations: Integration[];
  channels: SocialChannel[];
  agents: ProjectAgent[];
  goals: ProjectGoal[];
  alerts: ProjectAlert[];
  tasks: ProjectTask[];
  memory_entries: string[];
  next_actions: string[];
  blockers: string[];
}

const PROTOTYPE_PROJECTS: Record<string, ProjectData> = {
  "rouge-pivoine": {
    id: "rouge-pivoine",
    name: "Rouge Pivoine",
    type: "shopify",
    status: "active",
    priority: 5,
    description: "Boutique e-commerce florale sur Shopify. Thème Kalles v4.3.6 en live. Thème draft Rouge Pivoine en développement.",
    domains: ["rouge-pivoine.fr"],
    repo: "exnihilo042/rouge-pivoine-theme",
    drive: "Mon Drive/Clients/Rouge Pivoine",
    health_score: 72,
    integrations: [
      { tool: "Shopify",          status: "connected",      ref: "rouge-pivoine.myshopify.com",    detail: "Kalles v4.3.6 live · Draft en dev" },
      { tool: "GitHub",           status: "connected",      ref: "rouge-pivoine-theme",             detail: "branch: codex/import-..." },
      { tool: "Google Search Console", status: "not_configured", detail: "Configurer pour données SEO réelles" },
      { tool: "Google Analytics", status: "not_configured", detail: "Configurer pour trafic réel" },
      { tool: "Stripe",           status: "not_configured", detail: "Shopify Payments utilisé" },
    ],
    channels: [
      { platform: "instagram", handle: "rougepivoine", configured: true, followers: 1240, last_post: "2026-05-18" },
      { platform: "facebook",  handle: "rougepivoine", configured: true, followers: 680 },
      { platform: "pinterest", configured: false },
      { platform: "tiktok",    configured: false },
    ],
    agents: [
      { role: "Dev Agent",     engine: "claude_code",    autonomy: "supervisé",  last_activity: "2026-05-20", status: "active" },
      { role: "SEO Agent",     engine: "claude_code",    autonomy: "supervisé",  last_activity: "2026-05-15", status: "idle" },
    ],
    goals: [
      { label: "CA mensuel",          target: 2000,  current: 1200, unit: "€",            trend: "up" },
      { label: "Trafic organique",    target: 5000,  current: 3800, unit: "visites/mois", trend: "stable" },
      { label: "Positions top 10",    target: 20,    current: 8,    unit: "mots-clés",    trend: "up" },
      { label: "Commandes mensuelles",target: 40,    current: 28,   unit: "commandes",    trend: "up" },
    ],
    alerts: [
      { severity: "warn",  message: "Thème draft non poussé sur GitHub", action: "Pousser le thème draft sur le repo" },
      { severity: "info",  message: "Search Console non configurée", action: "Ajouter la propriété rouge-pivoine.fr" },
    ],
    tasks: [
      { label: "Pousser thème draft sur GitHub", status: "pending" },
      { label: "Validation client thème draft",  status: "pending" },
      { label: "Configurer Google Search Console", status: "blocked" },
      { label: "Import thème initial",           status: "done" },
      { label: "Audit thème Kalles existant",    status: "done" },
    ],
    memory_entries: [
      "§proj:rouge-pivoine|theme_live:Kalles_v4.3.6(138183049369)",
      "§proj:rouge-pivoine|theme_draft:Rouge_Pivoine_Draft(185968951677)",
      "§proj:rouge-pivoine|branch:codex/import-rouge-pivoine-theme-20260425",
      "§proj:rouge-pivoine|store:rouge-pivoine.myshopify.com",
    ],
    next_actions: [
      "Pousser le thème draft sur GitHub (branch dédiée)",
      "Envoyer lien de prévisualisation au client",
      "Configurer Google Search Console pour données SEO réelles",
    ],
    blockers: [],
  },

  "placerr": {
    id: "placerr",
    name: "Placerr",
    type: "saas",
    status: "active",
    priority: 1,
    description: "MVP SaaS — visualisation et réservation de places. Next.js + Pixi.js. 6 variants de design à valider.",
    domains: ["placerr.app"],
    repo: "exnihilo042/placerr",
    drive: "Mon Drive/Projets/Placerr",
    health_score: 55,
    integrations: [
      { tool: "GitHub",  status: "connected", ref: "exnihilo042/placerr" },
      { tool: "Vercel",  status: "configured", ref: "placerr.app", detail: "Déploiement auto depuis main" },
      { tool: "Stripe",  status: "not_configured", detail: "À configurer pour MVP paiement" },
    ],
    channels: [
      { platform: "linkedin", configured: false },
      { platform: "x",        configured: false },
    ],
    agents: [
      { role: "Dev Agent", engine: "claude_code", autonomy: "supervisé", last_activity: "2026-05-19", status: "active" },
    ],
    goals: [
      { label: "Design validé",       target: 1,   current: 0,   unit: "variante",     trend: "stable" },
      { label: "MVP beta utilisateurs", target: 10, current: 0,   unit: "beta users",   trend: "stable" },
    ],
    alerts: [
      { severity: "warn", message: "6 variantes design en attente de validation", action: "Clément choisit une variante" },
    ],
    tasks: [
      { label: "Créer 6 variantes de design (v1-v6)", status: "done" },
      { label: "Clément valide une variante",         status: "blocked" },
      { label: "Développer MVP depuis variante choisie", status: "pending" },
    ],
    memory_entries: [
      "§proj:placerr|stack:Next.js(web/)+Pixi.js",
      "§proj:placerr|state:6_design_variants_v1-v6_à_choisir",
      "§proj:placerr|next:Clément_choisit_variante",
    ],
    next_actions: ["Clément valide une variante de design (v1-v6)"],
    blockers: ["Choix de variante design en attente de Clément"],
  },
};

const FALLBACK_PROJECT: ProjectData = {
  id: "unknown",
  name: "Projet inconnu",
  type: "other",
  status: "pending",
  priority: 99,
  description: "Ce projet n'a pas encore de données configurées dans le Project Control Center.",
  domains: [],
  health_score: 0,
  integrations: [],
  channels: [],
  agents: [],
  goals: [],
  alerts: [{ severity: "info", message: "Configurer ce projet via le wizard de création" }],
  tasks: [],
  memory_entries: [],
  next_actions: ["Configurer le projet via /dashboard/projects/new"],
  blockers: [],
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function HealthBar({ score }: { score: number }) {
  const color = score >= 80 ? "var(--green)" : score >= 50 ? "var(--yellow)" : "var(--red)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ flex: 1, height: 5, background: "var(--surface-2)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.3s" }} />
      </div>
      <span style={{ fontSize: 14, fontWeight: 700, color, minWidth: 36 }}>{score}%</span>
    </div>
  );
}

function GoalRow({ goal }: { goal: ProjectGoal }) {
  const pct = Math.min(100, Math.round((goal.current / goal.target) * 100));
  const color = pct >= 80 ? "var(--green)" : pct >= 50 ? "var(--yellow)" : "var(--muted)";
  const trendIcon = goal.trend === "up" ? "↑" : goal.trend === "down" ? "↓" : "→";
  const trendColor = goal.trend === "up" ? "var(--green)" : goal.trend === "down" ? "var(--red)" : "var(--border)";

  return (
    <div style={{ padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 12, color: "var(--text)" }}>{goal.label}</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: trendColor }}>{trendIcon}</span>
          <span style={{ fontSize: 12, color: "var(--muted)" }}>
            {goal.current.toLocaleString("fr-FR")} / {goal.target.toLocaleString("fr-FR")} {goal.unit}
          </span>
          <span style={{ fontSize: 11, fontWeight: 700, color }}>{pct}%</span>
        </div>
      </div>
      <div style={{ height: 4, background: "var(--surface-2)", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2 }} />
      </div>
    </div>
  );
}

function AlertRow({ alert }: { alert: ProjectAlert }) {
  const color = alert.severity === "error" ? "var(--red)" : alert.severity === "warn" ? "var(--yellow)" : "var(--blue)";
  return (
    <div style={{ display: "flex", gap: 10, padding: "8px 12px", background: `color-mix(in srgb, ${color} 6%, transparent)`, borderLeft: `3px solid ${color}`, borderRadius: "0 4px 4px 0", marginBottom: 6 }}>
      <span style={{ fontSize: 9, color, marginTop: 3, flexShrink: 0 }}>●</span>
      <div>
        <div style={{ fontSize: 12, color: "var(--text)" }}>{alert.message}</div>
        {alert.action && <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>→ {alert.action}</div>}
      </div>
    </div>
  );
}

function AgentRow({ agent }: { agent: ProjectAgent }) {
  const statusColor = agent.status === "active" ? "var(--green)" : agent.status === "blocked" ? "var(--red)" : "var(--border)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 0", borderBottom: "1px solid var(--border)" }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: statusColor, flexShrink: 0, display: "inline-block" }} />
      <span style={{ flex: 1, fontSize: 12, color: "var(--text)", fontWeight: 500 }}>{agent.role}</span>
      <span style={{ fontSize: 11, color: "var(--muted)", fontFamily: "monospace" }}>{agent.engine}</span>
      <span style={{ fontSize: 10, color: "var(--border)" }}>{agent.autonomy}</span>
      {agent.last_activity && (
        <span style={{ fontSize: 10, color: "var(--border)" }}>{agent.last_activity}</span>
      )}
    </div>
  );
}

function TaskRow({ task }: { task: ProjectTask }) {
  const icon = task.status === "done" ? "✓" : task.status === "blocked" ? "⚠" : "○";
  const color = task.status === "done" ? "var(--green)" : task.status === "blocked" ? "var(--red)" : "var(--muted)";
  return (
    <div style={{ display: "flex", gap: 8, padding: "7px 0", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
      <span style={{ color, fontWeight: 700, flexShrink: 0, minWidth: 14 }}>{icon}</span>
      <span style={{ color: task.status === "done" ? "var(--muted)" : "var(--text)", textDecoration: task.status === "done" ? "line-through" : "none" }}>
        {task.label}
      </span>
    </div>
  );
}

const TYPE_ICON: Record<string, string> = {
  shopify: "◼", saas: "◳", mobile: "◾", site: "◱", agency: "◈", other: "◻",
};

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ProjectDetailPage({
  params,
}: {
  params: { projectId: string };
}) {
  const project = PROTOTYPE_PROJECTS[params.projectId] ?? FALLBACK_PROJECT;
  const isPrototype = params.projectId in PROTOTYPE_PROJECTS;

  return (
    <div style={{ maxWidth: 1000 }}>
      <PageHeader
        title={`${TYPE_ICON[project.type] ?? "◻"} ${project.name}`}
        subtitle={`${project.type} · P${project.priority} · ${project.domains.join(", ") || "Aucun domaine"}`}
      >
        <Badge label={project.status} variant={project.status === "active" ? "green" : project.status === "building" ? "yellow" : "muted"} />
        <Link href="/dashboard/projects" style={{ fontSize: 11, color: "var(--muted)", textDecoration: "none", padding: "4px 10px", border: "1px solid var(--border)", borderRadius: 4 }}>
          ← Projets
        </Link>
      </PageHeader>

      <InsetNotice
        icon="◱"
        text="Données prototype — fiche projet mockée"
        detail={`Endpoint futur : POST /api/projects/detail { id: "${project.id}" } · Scope Codex P2`}
        variant={isPrototype ? "muted" : "yellow"}
      />

      {/* ── Santé + résumé ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 20 }}>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 10, letterSpacing: 0.5, textTransform: "uppercase" }}>Santé projet</div>
          <HealthBar score={project.health_score} />
          {project.description && (
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 12, lineHeight: 1.5 }}>{project.description}</div>
          )}
        </div>

        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 10, letterSpacing: 0.5, textTransform: "uppercase" }}>Résumé</div>
          {[
            { label: "Intégrations",  value: `${project.integrations.filter((i) => i.status === "connected").length}/${project.integrations.length} OK`, color: "var(--green)" },
            { label: "Réseaux",       value: `${project.channels.filter((c) => c.configured).length}/${project.channels.length} configurés`, color: "var(--blue)" },
            { label: "Agents",        value: project.agents.length, color: "var(--accent)" },
            { label: "Alertes",       value: project.alerts.length, color: project.alerts.length > 0 ? "var(--yellow)" : "var(--green)" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
              <span style={{ color: "var(--muted)" }}>{label}</span>
              <span style={{ color, fontWeight: 600 }}>{value}</span>
            </div>
          ))}
        </div>

        {project.next_actions.length > 0 && (
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 10, letterSpacing: 0.5, textTransform: "uppercase" }}>Prochaines actions</div>
            {project.next_actions.map((action, i) => (
              <div key={i} style={{ fontSize: 12, color: "var(--text)", padding: "5px 0", borderBottom: i < project.next_actions.length - 1 ? "1px solid var(--border)" : "none", display: "flex", gap: 8 }}>
                <span style={{ color: "var(--accent)", flexShrink: 0 }}>→</span>
                <span>{action}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Alertes ── */}
      {project.alerts.length > 0 && (
        <ProjectSection title="Alertes" icon="⚠">
          {project.alerts.map((alert, i) => <AlertRow key={i} alert={alert} />)}
        </ProjectSection>
      )}

      {/* ── Objectifs & KPIs ── */}
      {project.goals.length > 0 && (
        <ProjectSection title="Objectifs & KPIs" icon="◉">
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "0 16px" }}>
            {project.goals.map((goal, i) => <GoalRow key={i} goal={goal} />)}
          </div>
        </ProjectSection>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 20 }}>
        {/* ── Intégrations ── */}
        <ProjectSection title="Outils connectés" icon="◱">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {project.integrations.map((integration, i) => (
              <div key={i}>
                <IntegrationBadge tool={integration.tool} status={integration.status} ref={integration.ref} />
                {integration.detail && (
                  <div style={{ fontSize: 10, color: "var(--border)", marginTop: 2, marginLeft: 22 }}>{integration.detail}</div>
                )}
              </div>
            ))}
          </div>
        </ProjectSection>

        {/* ── Réseaux sociaux ── */}
        <ProjectSection title="Réseaux sociaux" icon="◲">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {project.channels.map((ch, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2 }}>
                <SocialChannelPill platform={ch.platform} handle={ch.handle} configured={ch.configured} />
                {ch.followers && (
                  <span style={{ fontSize: 9, color: "var(--border)", marginLeft: 4 }}>{ch.followers.toLocaleString("fr-FR")} abonnés</span>
                )}
              </div>
            ))}
          </div>
        </ProjectSection>

        {/* ── Agents ── */}
        {project.agents.length > 0 && (
          <ProjectSection title="Agents ATHOS" icon="⬡">
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "0 12px" }}>
              {project.agents.map((agent, i) => <AgentRow key={i} agent={agent} />)}
            </div>
          </ProjectSection>
        )}

        {/* ── Tasks ── */}
        {project.tasks.length > 0 && (
          <ProjectSection title="Tâches / Roadmap" icon="◫">
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "0 12px" }}>
              {project.tasks.map((task, i) => <TaskRow key={i} task={task} />)}
            </div>
          </ProjectSection>
        )}
      </div>

      {/* ── Mémoire ── */}
      {project.memory_entries.length > 0 && (
        <ProjectSection title="Mémoire §-format" icon="◪">
          <div style={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 6, padding: "10px 14px" }}>
            {project.memory_entries.map((entry, i) => (
              <div key={i} style={{ fontSize: 11, fontFamily: "monospace", color: "var(--muted)", padding: "3px 0", borderBottom: i < project.memory_entries.length - 1 ? "1px solid var(--border)" : "none" }}>
                {entry}
              </div>
            ))}
          </div>
        </ProjectSection>
      )}

      {/* ── Présence numérique ── */}
      <ProjectSection title="Présence numérique" icon="◳">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {project.domains.map((d) => (
            <span key={d} style={{ fontSize: 12, padding: "4px 10px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "monospace", color: "var(--text)" }}>
              🌐 {d}
            </span>
          ))}
          {project.repo && (
            <span style={{ fontSize: 12, padding: "4px 10px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "monospace", color: "var(--text)" }}>
              ⎇ {project.repo}
            </span>
          )}
          {project.drive && (
            <span style={{ fontSize: 12, padding: "4px 10px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 6, fontFamily: "monospace", color: "var(--muted)" }}>
              ◳ {project.drive}
            </span>
          )}
        </div>
      </ProjectSection>
    </div>
  );
}
