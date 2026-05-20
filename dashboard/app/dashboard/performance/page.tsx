import { athosPost } from "@/lib/athos";
import { Card, StatCard, MockBanner, Gauge, SectionLabel, PageHeader, DataRow, Badge } from "@/components/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ObsPayload {
  server_runtime?: { pid?: number; uptime_seconds?: number; started_at?: string };
  failover?: { ts?: string; label?: string; result?: string }[];
  memory?: { ok?: boolean; missing?: string[] };
  git?: { branch?: string; head?: string; dirty?: string[] };
  summary?: {
    listening_ports?: number;
    launchd_jobs?: number;
    agent_processes?: number;
    attached_engines?: number;
    installed_skills?: number;
    loop_running?: boolean;
    capability_graph_nodes?: number;
  };
}

interface StatusPayload {
  engine?: string;
  degraded?: boolean;
  available?: string[];
  budget?: number;
}

// ── Mock data — clearly identified ────────────────────────────────────────────
// Source future : Lighthouse CLI, Google PageSpeed Insights API
// Endpoint à créer : /api/performance (scope Codex)

const MOCK_LIGHTHOUSE = [
  {
    site: "ex-nihilo.agency",
    perf: 74,
    a11y: 89,
    seo: 92,
    bp: 83,
    mobile: 62,
  },
  {
    site: "rouge-pivoine.fr",
    perf: 61,
    a11y: 78,
    seo: 88,
    bp: 79,
    mobile: 54,
  },
  {
    site: "placerr.app",
    perf: 0,
    a11y: 0,
    seo: 0,
    bp: 0,
    mobile: 0,
    nodata: true,
  },
];

const MOCK_API_LATENCIES = [
  { endpoint: "/api/status",            p50: 45,  p95: 120, ok: true },
  { endpoint: "/api/observability",     p50: 78,  p95: 210, ok: true },
  { endpoint: "/api/conversation",      p50: 130, p95: 380, ok: true },
  { endpoint: "/api/capability_graph",  p50: 92,  p95: 250, ok: true },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatUptime(s: number): string {
  if (s >= 86400) return `${Math.floor(s / 86400)}j ${Math.floor((s % 86400) / 3600)}h`;
  if (s >= 3600)  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
}

function scoreColor(v: number): string {
  return v >= 80 ? "var(--green)" : v >= 50 ? "var(--yellow)" : "var(--red)";
}

// ── Score card ────────────────────────────────────────────────────────────────

function LighthouseScoreRow({ label, value }: { label: string; value: number }) {
  if (value === 0) return null;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "7px 0",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <span style={{ fontSize: 11, color: "var(--muted)", minWidth: 80 }}>{label}</span>
      <div style={{ flex: 1 }}>
        <div
          style={{
            height: 5,
            background: "var(--surface-2)",
            borderRadius: 3,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${value}%`,
              background: scoreColor(value),
              borderRadius: 3,
            }}
          />
        </div>
      </div>
      <span
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: scoreColor(value),
          minWidth: 28,
          textAlign: "right",
        }}
      >
        {value}
      </span>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function PerformancePage() {
  let obs: ObsPayload = {};
  let status: StatusPayload = {};

  try {
    [obs, status] = await Promise.all([
      athosPost<ObsPayload>("/api/observability"),
      athosPost<StatusPayload>("/api/status"),
    ]);
  } catch {}

  const uptime = obs.server_runtime?.uptime_seconds ?? 0;
  const failovers = (obs.failover ?? []).length;
  const memOk = obs.memory?.ok ?? false;
  const enginesAvail = (status.available ?? []).length;
  const degraded = status.degraded ?? false;

  // Health score: 4 criteria × 25 pts each
  const healthPts = [
    uptime > 3600,
    failovers === 0,
    memOk,
    enginesAvail > 0 && !degraded,
  ].filter(Boolean).length;
  const healthScore = healthPts * 25;

  const healthLabel =
    healthScore >= 100 ? "Optimal" :
    healthScore >= 75  ? "Bon" :
    healthScore >= 50  ? "Dégradé" :
    "Critique";

  const ports = obs.summary?.listening_ports ?? 0;
  const skills = obs.summary?.installed_skills ?? 0;
  const loopRunning = obs.summary?.loop_running ?? false;

  return (
    <div style={{ maxWidth: 1100 }}>
      <PageHeader
        title="Performance"
        subtitle="Supervision système & sites — Ex-Nihilo Agency"
      />

      {/* ── KPI système (REAL) ── */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Score santé"
          value={`${healthScore}/100`}
          sub={`RÉEL · ${healthLabel}`}
          color={scoreColor(healthScore)}
          size="lg"
        />
        <StatCard
          label="Uptime HUB"
          value={uptime > 0 ? formatUptime(uptime) : "—"}
          sub="RÉEL · :7474 ATHOS"
          color={uptime > 3600 ? "var(--green)" : "var(--yellow)"}
        />
        <StatCard
          label="Services actifs"
          value={ports > 0 ? ports : "—"}
          sub="RÉEL · ports en écoute"
          color={ports >= 3 ? "var(--green)" : "var(--yellow)"}
        />
        <StatCard
          label="Engines dispo"
          value={enginesAvail > 0 ? enginesAvail : degraded ? "dégradé" : "—"}
          sub="RÉEL · moteurs actifs"
          color={enginesAvail > 0 ? (degraded ? "var(--yellow)" : "var(--green)") : "var(--red)"}
        />
      </div>

      {/* ── Santé critères (REAL) ── */}
      <div className="grid-auto-2" style={{ marginBottom: 20 }}>
        <Card title="État système — RÉEL">
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[
              { label: "Uptime > 1h",         ok: uptime > 3600,       detail: uptime > 0 ? formatUptime(uptime) : "—" },
              { label: "Zéro failover",        ok: failovers === 0,     detail: failovers > 0 ? `${failovers} événement${failovers > 1 ? "s" : ""}` : "propre" },
              { label: "Mémoire ATHOS",        ok: memOk,               detail: memOk ? "OK" : `${(obs.memory?.missing ?? []).length} manquant(s)` },
              { label: "Engine disponible",    ok: enginesAvail > 0,    detail: (status.available ?? []).join(", ") || "—" },
            ].map(({ label, ok, detail }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 0",
                  borderBottom: "1px solid var(--border)",
                  fontSize: 13,
                }}
              >
                <span style={{ color: ok ? "var(--green)" : "var(--red)", fontSize: 10, flexShrink: 0 }}>●</span>
                <span style={{ flex: 1, color: "var(--text)" }}>{label}</span>
                <span style={{ color: "var(--muted)", fontSize: 12 }}>{detail}</span>
              </div>
            ))}
            <div style={{ marginTop: 8 }}>
              <Gauge value={healthScore} />
            </div>
          </div>
        </Card>

        <Card title="Infrastructure — RÉEL">
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {[
              {
                label: ":7474  ATHOS HUB",
                ok: uptime > 0,
                detail: `PID ${obs.server_runtime?.pid ?? "—"} · ${uptime > 0 ? formatUptime(uptime) : "—"}`,
              },
              {
                label: ":8765  agentmemory",
                ok: ports >= 2,
                detail: "Python memory service",
              },
              {
                label: ":3333  Next.js",
                ok: true,
                detail: "dashboard (ce process)",
              },
            ].map(({ label, ok, detail }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "8px 0",
                  borderBottom: "1px solid var(--border)",
                  fontSize: 12,
                }}
              >
                <span style={{ color: ok ? "var(--green)" : "var(--red)", fontSize: 9, flexShrink: 0 }}>●</span>
                <span style={{ flex: 1, fontFamily: "monospace", color: "var(--text)" }}>{label}</span>
                <span style={{ color: "var(--muted)", fontSize: 11 }}>{detail}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 2 }}>
            <DataRow
              label="Git branch"
              value={obs.git?.branch ?? "—"}
              mono
            />
            <DataRow
              label="Commit"
              value={obs.git?.head?.slice(0, 7) ?? "—"}
              mono
            />
            <DataRow
              label="Skills installés"
              value={skills > 0 ? `${skills}` : "—"}
              color={skills > 0 ? "var(--green)" : "var(--muted)"}
            />
            <DataRow
              label="Loop autonome"
              value={loopRunning ? "active" : "inactive"}
              color={loopRunning ? "var(--green)" : "var(--muted)"}
            />
          </div>
          {(obs.git?.dirty?.length ?? 0) > 0 && (
            <div style={{ marginTop: 10, fontSize: 11, color: "var(--yellow)" }}>
              ⚠ Repo dirty — {obs.git!.dirty!.length} fichier{obs.git!.dirty!.length > 1 ? "s" : ""} modifié{obs.git!.dirty!.length > 1 ? "s" : ""}
            </div>
          )}
        </Card>
      </div>

      {/* ── Lighthouse (MOCK) ── */}
      <MockBanner message="Scores Lighthouse fictifs. Brancher Lighthouse CLI ou Google PageSpeed Insights API pour les vraies métriques." />

      <div style={{ marginBottom: 20 }}>
        <SectionLabel>Sites — Lighthouse {"{"}MOCK{"}"}</SectionLabel>
        <div className="grid-auto-2">
          {MOCK_LIGHTHOUSE.filter((s) => !s.nodata).map((site) => (
            <Card key={site.site} title={`${site.site} · MOCK`}>
              <LighthouseScoreRow label="Performance" value={site.perf} />
              <LighthouseScoreRow label="Accessibilité" value={site.a11y} />
              <LighthouseScoreRow label="SEO" value={site.seo} />
              <LighthouseScoreRow label="Bonnes pratiques" value={site.bp} />
              <div
                style={{
                  marginTop: 12,
                  display: "flex",
                  gap: 8,
                  alignItems: "center",
                }}
              >
                <span style={{ fontSize: 11, color: "var(--muted)" }}>Mobile :</span>
                <span
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: scoreColor(site.mobile),
                  }}
                >
                  {site.mobile}
                </span>
                <span style={{ fontSize: 11, color: "var(--border)" }}>/ 100</span>
              </div>
            </Card>
          ))}
          {MOCK_LIGHTHOUSE.filter((s) => s.nodata).map((site) => (
            <Card key={site.site} title={`${site.site} · MOCK`}>
              <div
                style={{
                  padding: "20px 0",
                  textAlign: "center",
                  color: "var(--border)",
                  fontSize: 13,
                }}
              >
                Non mesuré — site en développement
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* ── API latences (MOCK) ── */}
      <Card title="Latences API HUB — MOCK · à brancher">
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Endpoint", "p50 (ms)", "p95 (ms)", "Statut"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "8px 12px",
                      textAlign: h === "Endpoint" ? "left" : "right",
                      fontSize: 10,
                      letterSpacing: 1,
                      textTransform: "uppercase",
                      color: "var(--muted)",
                      fontWeight: 600,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_API_LATENCIES.map((row) => (
                <tr
                  key={row.endpoint}
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <td style={{ padding: "9px 12px", fontFamily: "monospace", color: "var(--text)" }}>
                    {row.endpoint}
                  </td>
                  <td style={{ padding: "9px 12px", textAlign: "right", color: "var(--text)", fontWeight: 600 }}>
                    {row.p50}
                  </td>
                  <td
                    style={{
                      padding: "9px 12px",
                      textAlign: "right",
                      color: row.p95 > 300 ? "var(--yellow)" : "var(--text)",
                    }}
                  >
                    {row.p95}
                  </td>
                  <td style={{ padding: "9px 12px", textAlign: "right" }}>
                    <Badge
                      label={row.ok ? "OK" : "KO"}
                      variant={row.ok ? "green" : "red"}
                      dot
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ padding: "8px 12px", fontSize: 11, color: "var(--border)" }}>
          ⚠ MOCK — Implémenter un middleware de mesure côté HUB pour les vraies latences
        </div>
      </Card>

      <div style={{ marginTop: 16, fontSize: 11, color: "var(--border)" }}>
        ⚠ Score santé et infra sont RÉELS · Lighthouse et latences API sont MOCK — Source future : Lighthouse CLI + /api/performance (Codex)
      </div>
    </div>
  );
}
