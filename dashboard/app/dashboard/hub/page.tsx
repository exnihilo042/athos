import { athosPost } from "@/lib/athos";
import RefreshButton from "@/components/RefreshButton";
import LiveFeed from "@/components/LiveFeed";
import { Card, StatCard, Badge, SectionLabel, DataRow, PageHeader } from "@/components/ui";
import Link from "next/link";

// ── Types ─────────────────────────────────────────────────────────────────────

interface StatusPayload {
  engine?: string;
  degraded?: boolean;
  budget?: number;
  available?: string[];
  capability_graph?: {
    summary?: {
      nodes?: number;
      edges?: number;
      available_nodes?: number;
      offline_ready_nodes?: number;
      austere_mode_ready?: boolean;
      interconnection_score?: number;
    };
  };
  session?: {
    events?: number;
    exchanges?: number;
    actions?: number;
    recent_summary?: string;
  };
  spend_policy?: {
    mode?: string;
    room_auto_respond?: boolean;
    room_auto_respond_engines?: string[];
    autonomous_loop_enabled?: boolean;
  };
}

interface ObsPayload {
  git?: { head?: string; branch?: string; dirty?: unknown[] };
  server_runtime?: { pid?: number; uptime_seconds?: number };
  memory?: { ok?: boolean; missing?: string[] };
  failover?: { ts?: string; label?: string; result?: string }[];
  summary?: {
    listening_ports?: number;
    launchd_jobs?: number;
    failover_events?: number;
    installed_skills?: number;
    capability_graph_nodes?: number;
    loop_running?: boolean;
  };
}

interface RespondersPayload {
  actors?: {
    claude?: { available?: boolean; last_problem?: { kind?: string } };
    codex?: { available?: boolean; last_problem?: { kind?: string; content?: string } };
  };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatUptime(s: number): string {
  if (s >= 86400) return `${Math.floor(s / 86400)}j ${Math.floor((s % 86400) / 3600)}h`;
  if (s >= 3600)  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  if (s > 0)      return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
  return "—";
}

// ── Module quick-access card ──────────────────────────────────────────────────

function ModuleCard({
  href,
  icon,
  label,
  stat,
  statColor,
  badge,
}: {
  href: string;
  icon: string;
  label: string;
  stat?: string | number;
  statColor?: string;
  badge?: "green" | "yellow" | "red" | "muted";
}) {
  return (
    <Link
      href={href}
      style={{ textDecoration: "none" }}
    >
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "12px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 8,
          cursor: "pointer",
          transition: "border-color 0.15s",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <span style={{ fontSize: 18, color: "var(--muted)" }}>{icon}</span>
          {badge && (
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background:
                  badge === "green" ? "var(--green)" :
                  badge === "yellow" ? "var(--yellow)" :
                  badge === "red" ? "var(--red)" :
                  "var(--border)",
                flexShrink: 0,
                marginTop: 2,
              }}
            />
          )}
        </div>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text)", marginBottom: 2 }}>{label}</div>
          {stat !== undefined && (
            <div style={{ fontSize: 11, color: statColor ?? "var(--muted)" }}>{stat}</div>
          )}
        </div>
      </div>
    </Link>
  );
}

// ── Product status row ─────────────────────────────────────────────────────────

function ProductRow({
  icon,
  page,
  status,
  source,
  dep,
}: {
  icon: string;
  page: string;
  status: "real" | "mixed" | "mock" | "static";
  source: string;
  dep?: string;
}) {
  const STATUS_MAP = {
    real:   { label: "RÉEL",    variant: "green" as const },
    mixed:  { label: "MIXTE",   variant: "yellow" as const },
    mock:   { label: "MOCK",    variant: "muted" as const },
    static: { label: "STATIQUE",variant: "blue" as const },
  };
  const s = STATUS_MAP[status];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 12px",
        borderBottom: "1px solid var(--border)",
        fontSize: 12,
        flexWrap: "wrap",
      }}
    >
      <span style={{ color: "var(--muted)", fontSize: 11, minWidth: 14 }}>{icon}</span>
      <span style={{ flex: 1, color: "var(--text)", minWidth: 100 }}>{page}</span>
      <Badge label={s.label} variant={s.variant} />
      <span style={{ color: "var(--muted)", fontSize: 11, minWidth: 120 }}>{source}</span>
      {dep && (
        <span style={{ fontSize: 10, color: "var(--border)", fontStyle: "italic" }}>{dep}</span>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function HubPage() {
  let status: StatusPayload = {};
  let obs: ObsPayload = {};
  let responders: RespondersPayload = {};

  try {
    [status, obs] = await Promise.all([
      athosPost<StatusPayload>("/api/status"),
      athosPost<ObsPayload>("/api/observability"),
    ]);
  } catch {}

  try {
    const r = await athosPost<{ actors?: RespondersPayload["actors"] }>("/api/observability", { scope: "responders" });
    responders = { actors: r?.actors };
  } catch {}

  const uptime = obs.server_runtime?.uptime_seconds ?? 0;
  const graphSummary = status.capability_graph?.summary;
  const claudeOk = responders.actors?.claude?.available ?? false;
  const codexOk = responders.actors?.codex?.available ?? false;
  const failoverCount = obs.failover?.length ?? obs.summary?.failover_events ?? 0;
  const memOk = obs.memory?.ok ?? true;
  const loopRunning = obs.summary?.loop_running ?? false;

  return (
    <div style={{ maxWidth: 1200 }}>
      <PageHeader title="Vue Centrale" subtitle="Centre de contrôle ATHOS — état temps réel">
        <RefreshButton />
      </PageHeader>

      {/* ── KPI système (REAL) ── */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Moteur actif"
          value={status.engine ?? "—"}
          sub={status.degraded ? "⚠ dégradé" : "opérationnel"}
          color={status.degraded ? "var(--yellow)" : "var(--accent)"}
          size="lg"
        />
        <StatCard
          label="Uptime HUB"
          value={formatUptime(uptime)}
          sub={`PID ${obs.server_runtime?.pid ?? "—"}`}
          color={uptime > 3600 ? "var(--green)" : "var(--yellow)"}
        />
        <StatCard
          label="Budget ATHOS"
          value={status.budget !== undefined ? `${status.budget.toFixed(4)} €` : "—"}
          sub={status.spend_policy?.mode ?? "zero_paid_api"}
          color="var(--muted)"
        />
        <StatCard
          label="Alertes système"
          value={failoverCount > 0 ? failoverCount : memOk ? "0" : "⚠"}
          sub={failoverCount > 0 ? "failovers récents" : memOk ? "système propre" : "mémoire incomplète"}
          color={failoverCount > 0 || !memOk ? "var(--yellow)" : "var(--green)"}
        />
      </div>

      {/* ── État détaillé (REAL) ── */}
      <div className="grid-auto-2" style={{ marginBottom: 20 }}>
        <Card title="Moteur & Responders">
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Engine actif</span>
              <span style={{ fontSize: 14, fontWeight: 700, color: "var(--accent)" }}>
                {status.engine ?? "—"}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Disponibles</span>
              <span style={{ fontSize: 12, color: "var(--text)" }}>
                {(status.available ?? []).join(", ") || "—"}
              </span>
            </div>
          </div>
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              { label: "claude", ok: claudeOk, problem: responders.actors?.claude?.last_problem?.kind },
              { label: "codex", ok: codexOk, problem: responders.actors?.codex?.last_problem?.kind ?? responders.actors?.codex?.last_problem?.content },
            ].map(({ label, ok, problem }) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, color: "var(--muted)" }}>{label}</span>
                <Badge
                  label={ok ? "disponible" : (problem ?? "bloqué")}
                  variant={ok ? "green" : "red"}
                  dot
                />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, borderTop: "1px solid var(--border)", paddingTop: 10, fontSize: 11, color: "var(--muted)" }}>
            Auto-respond: <span style={{ color: status.spend_policy?.room_auto_respond ? "var(--green)" : "var(--border)" }}>
              {status.spend_policy?.room_auto_respond ? "actif" : "inactif"}
            </span>
            {" · "}Loop: <span style={{ color: loopRunning ? "var(--green)" : "var(--border)" }}>
              {loopRunning ? "active" : "inactive"}
            </span>
          </div>
        </Card>

        <Card title="Graphe & Session">
          {graphSummary ? (
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", gap: 16, marginBottom: 10 }}>
                {[
                  { v: graphSummary.available_nodes, l: "disponibles", c: "var(--green)" },
                  { v: graphSummary.nodes, l: "total", c: "var(--text)" },
                  { v: graphSummary.offline_ready_nodes, l: "offline-ready", c: "var(--blue)" },
                ].map(({ v, l, c }) => (
                  <div key={l}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: c }}>{v ?? "—"}</div>
                    <div style={{ fontSize: 10, color: "var(--muted)" }}>{l}</div>
                  </div>
                ))}
              </div>
              <Badge
                label={graphSummary.austere_mode_ready ? "austere mode ✓" : "austere mode ✗"}
                variant={graphSummary.austere_mode_ready ? "green" : "red"}
              />
            </div>
          ) : (
            <div style={{ color: "var(--muted)", fontSize: 13, marginBottom: 12 }}>Graph non disponible</div>
          )}
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, display: "flex", gap: 20 }}>
            {[
              { label: "Events", value: status.session?.events },
              { label: "Échanges", value: status.session?.exchanges },
              { label: "Actions", value: status.session?.actions },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text)" }}>{value ?? "—"}</div>
                <div style={{ fontSize: 10, color: "var(--muted)" }}>{label}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Infrastructure">
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {[
              { label: ":7474 ATHOS HUB", ok: uptime > 0, detail: `PID ${obs.server_runtime?.pid ?? "—"} · ${formatUptime(uptime)}` },
              { label: ":8765 agentmemory", ok: (obs.summary?.listening_ports ?? 0) >= 2, detail: "Python memory" },
              { label: ":3333 Next.js", ok: true, detail: "dashboard" },
            ].map(({ label, ok, detail }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 0", borderBottom: "1px solid var(--border)", fontSize: 12 }}>
                <span style={{ color: ok ? "var(--green)" : "var(--red)", fontSize: 9 }}>●</span>
                <span style={{ flex: 1, fontFamily: "monospace", color: "var(--text)" }}>{label}</span>
                <span style={{ color: "var(--muted)", fontSize: 11 }}>{detail}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, fontSize: 11, color: "var(--muted)" }}>
            Git: <span style={{ fontFamily: "monospace", color: "var(--text)" }}>
              {obs.git?.branch ?? "—"} @ {obs.git?.head?.slice(0, 7) ?? "—"}
            </span>
            {(obs.git?.dirty?.length ?? 0) > 0 && (
              <span style={{ color: "var(--yellow)" }}> · dirty</span>
            )}
          </div>
        </Card>

        <Card title="Mémoire & Système">
          <DataRow
            label="Mémoire ATHOS"
            value={memOk ? "OK" : `${(obs.memory?.missing ?? []).length} manquant(s)`}
            color={memOk ? "var(--green)" : "var(--red)"}
          />
          <DataRow
            label="Ports actifs"
            value={obs.summary?.listening_ports ?? "—"}
          />
          <DataRow
            label="Launchd jobs"
            value={obs.summary?.launchd_jobs ?? "—"}
          />
          <DataRow
            label="Skills installés"
            value={obs.summary?.installed_skills ?? "—"}
            color={obs.summary?.installed_skills ? "var(--green)" : "var(--muted)"}
          />
          <DataRow
            label="Politique dépense"
            value={status.spend_policy?.mode ?? "—"}
            mono
          />
        </Card>
      </div>

      {/* ── Accès rapide modules ── */}
      <div style={{ marginBottom: 20 }}>
        <SectionLabel>Modules dashboard</SectionLabel>
        <div className="grid-auto-4" style={{ gap: 10 }}>
          <ModuleCard href="/dashboard/projects"     icon="◱" label="Sites & Projets"  stat="Project Control Center · P2"  badge="green" />
          <ModuleCard href="/dashboard/projects/new" icon="◈" label="Nouveau projet"   stat="Wizard 7 étapes · prototype"  badge="yellow" />
          <ModuleCard href="/dashboard/roadmap"    icon="◪" label="Roadmap"          stat="15 items P0–P4"              badge="green" />
          <ModuleCard href="/dashboard/performance" icon="◳" label="Performance"     stat="santé système + Lighthouse"  badge="yellow" />
          <ModuleCard href="/dashboard/crm"        icon="◾" label="CRM / Clients"   stat="4 clients — MOCK"            badge="yellow" />
          <ModuleCard href="/dashboard/finances"   icon="◻" label="Finances"         stat="budget réel + CA mock"       badge="yellow" />
          <ModuleCard href="/dashboard/seo"        icon="◲" label="SEO Analytics"    stat="MOCK · 5 actions IA P0-P2"   badge="muted" />
          <ModuleCard href="/dashboard/commandes"  icon="◼" label="Commandes"        stat="pipeline agence — MOCK"       badge="muted" />
          <ModuleCard href="/dashboard/skills"     icon="⬡" label="Skills & Capacités" stat="47 skills — catalogue local" badge="green" />
          <ModuleCard href="/dashboard/alerts"     icon="⚠" label="Alertes"
            stat={failoverCount > 0 ? `${failoverCount} failover(s)` : "système propre"}
            statColor={failoverCount > 0 ? "var(--yellow)" : "var(--green)"}
            badge={failoverCount > 0 ? "yellow" : "green"}
          />
        </div>
      </div>

      {/* ── État produit ── */}
      <div style={{ marginBottom: 20 }}>
        <SectionLabel>État produit dashboard</SectionLabel>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          <div style={{ display: "flex", padding: "8px 12px", borderBottom: "1px solid var(--border)", background: "var(--surface-2)" }}>
            {["Module", "Statut", "Source actuelle", "Dépendance"].map((h, i) => (
              <span key={h} style={{ fontSize: 10, letterSpacing: 1, textTransform: "uppercase", color: "var(--border)", fontWeight: 600, flex: i === 0 ? 1 : i === 2 ? "0 0 120px" : "0 0 auto", minWidth: i === 3 ? 100 : undefined, marginRight: i < 3 ? 10 : 0 }}>{h}</span>
            ))}
          </div>
          <ProductRow icon="◈" page="Hub — Vue Centrale"   status="real"   source="/api/status + /api/observability" />
          <ProductRow icon="◉" page="Room"                 status="real"   source="/api/conversation, /api/message" />
          <ProductRow icon="⬡" page="Agents IA"            status="real"   source="/api/capability_graph" />
          <ProductRow icon="⚠" page="Alertes"              status="real"   source="/api/observability" />
          <ProductRow icon="◱" page="Sites & Projets"      status="real"   source="/api/projects" dep="PCC liste enrichie" />
          <ProductRow icon="◈" page="PCC — Nouveau projet" status="static" source="prototype frontend" dep="/api/projects/create (Codex P2)" />
          <ProductRow icon="◈" page="PCC — Détail projet"  status="static" source="prototype frontend" dep="/api/projects/detail (Codex P2)" />
          <ProductRow icon="⊙" page="Paramètres"           status="real"   source="/api/settings" />
          <ProductRow icon="⟳" page="Automations"          status="real"   source="/api/loop, /api/skills" />
          <ProductRow icon="◫" page="Rapports"             status="real"   source="/api/report" dep="endpoint à enrichir" />
          <ProductRow icon="◳" page="Performance"          status="mixed"  source="Santé réel + Lighthouse MOCK" dep="Lighthouse CLI (Codex)" />
          <ProductRow icon="◻" page="Finances"             status="mixed"  source="Budget réel + CA MOCK" dep="Stripe/Shopify API" />
          <ProductRow icon="◲" page="SEO Analytics"        status="mock"   source="données MOCK" dep="GSC API (Codex)" />
          <ProductRow icon="◼" page="Commandes"            status="mock"   source="données MOCK" dep="Décision source (Clément)" />
          <ProductRow icon="◾" page="CRM / Clients"        status="mock"   source="données MOCK" dep="/api/crm (Codex)" />
          <ProductRow icon="◪" page="Roadmap"              status="static" source="données statiques 2026-05-20" dep="mise à jour manuelle" />
          <ProductRow icon="⬡" page="Skills & Capacités"  status="static" source="skill-registry.ts (local)" dep="API Codex P3" />
        </div>
      </div>

      {/* ── Failovers récents ── */}
      {(obs.failover?.length ?? 0) > 0 && (
        <div style={{ marginBottom: 20 }}>
          <SectionLabel count={obs.failover!.length}>Failovers récents</SectionLabel>
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
            {obs.failover!.slice(-4).reverse().map((f, i) => (
              <div key={i} style={{ display: "flex", gap: 12, fontSize: 12, padding: "10px 16px", borderBottom: i < Math.min(3, (obs.failover?.length ?? 1) - 1) ? "1px solid var(--border)" : "none" }}>
                <span style={{ color: "var(--border)", minWidth: 130, flexShrink: 0 }}>
                  {f.ts ? new Date(f.ts).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"}
                </span>
                <span style={{ color: "var(--yellow)" }}>{f.label}</span>
                <span style={{ color: "var(--muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {f.result}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Live feed ── */}
      <LiveFeed />
    </div>
  );
}
