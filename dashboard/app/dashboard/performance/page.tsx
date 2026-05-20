import { athosPost } from "@/lib/athos";
import { Card, StatCard, Gauge, SectionLabel, PageHeader, DataRow, Badge, InsetNotice } from "@/components/ui";
import type { PerformanceRuntimePayload, LatencySample } from "@/lib/types";

// ── Types (local obs/status) ──────────────────────────────────────────────────

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

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatUptime(s: number): string {
  if (s >= 86400) return `${Math.floor(s / 86400)}j ${Math.floor((s % 86400) / 3600)}h`;
  if (s >= 3600)  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
}

function scoreColor(v: number): string {
  return v >= 80 ? "var(--green)" : v >= 50 ? "var(--yellow)" : "var(--red)";
}

// ── Latency row component ─────────────────────────────────────────────────────

function LatencyRow({ row }: { row: LatencySample }) {
  return (
    <tr style={{ borderBottom: "1px solid var(--border)" }}>
      <td style={{ padding: "9px 12px", fontFamily: "monospace", color: "var(--text)", fontSize: 12 }}>
        {row.endpoint}
      </td>
      <td style={{ padding: "9px 12px", textAlign: "right", color: "var(--text)", fontWeight: 600, fontSize: 12 }}>
        {row.p50.toFixed(1)}
      </td>
      <td
        style={{
          padding: "9px 12px",
          textAlign: "right",
          color: row.p95 > 300 ? "var(--yellow)" : "var(--text)",
          fontSize: 12,
        }}
      >
        {row.p95.toFixed(1)}
      </td>
      <td style={{ padding: "9px 12px", textAlign: "right" }}>
        <Badge label={row.ok ? "OK" : "KO"} variant={row.ok ? "green" : "red"} dot />
      </td>
    </tr>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function PerformancePage() {
  let obs: ObsPayload = {};
  let status: StatusPayload = {};
  let perf: PerformanceRuntimePayload | null = null;

  try {
    [obs, status, perf] = await Promise.all([
      athosPost<ObsPayload>("/api/observability"),
      athosPost<StatusPayload>("/api/status"),
      athosPost<PerformanceRuntimePayload>("/api/performance"),
    ]);
  } catch {}

  // Prefer performance endpoint data, fall back to observability
  const uptime = perf?.system?.uptime_seconds ?? obs.server_runtime?.uptime_seconds ?? 0;
  const failovers = (obs.failover ?? []).length;
  const memOk = perf?.system?.memory_ok ?? obs.memory?.ok ?? false;
  const enginesAvail = (status.available ?? []).length;
  const degraded = status.degraded ?? false;
  const loopRunning = perf?.system?.loop_running ?? obs.summary?.loop_running ?? false;
  const ports = perf?.system?.listening_ports ?? obs.summary?.listening_ports ?? 0;
  const skills = obs.summary?.installed_skills ?? 0;
  const pid = perf?.system?.server_pid ?? obs.server_runtime?.pid;

  // Real latency data from /api/performance (measured server-side)
  const latencies: LatencySample[] = perf?.api_latencies ?? [];
  const hasRealLatencies = latencies.length > 0;

  // Lighthouse: endpoint returns [] and lighthouse_configured: false
  const lighthouseConfigured = perf?.capabilities?.lighthouse_configured ?? false;

  // Health score
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

  return (
    <div style={{ maxWidth: 1100 }}>
      <PageHeader
        title="Performance"
        subtitle="Supervision système & sites — Ex-Nihilo Agency"
      />

      {/* ── KPI système (RÉEL) ── */}
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

      {/* ── État système + Infra (RÉEL) ── */}
      <div className="grid-auto-2" style={{ marginBottom: 20 }}>
        <Card title="État système — RÉEL">
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[
              { label: "Uptime > 1h",      ok: uptime > 3600,    detail: uptime > 0 ? formatUptime(uptime) : "—" },
              { label: "Zéro failover",     ok: failovers === 0,  detail: failovers > 0 ? `${failovers} événement${failovers > 1 ? "s" : ""}` : "propre" },
              { label: "Mémoire ATHOS",     ok: memOk,            detail: memOk ? "OK" : `${(obs.memory?.missing ?? []).length} manquant(s)` },
              { label: "Engine disponible", ok: enginesAvail > 0, detail: (status.available ?? []).join(", ") || "—" },
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
                detail: `PID ${pid ?? "—"} · ${uptime > 0 ? formatUptime(uptime) : "—"}`,
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
            <DataRow label="Git branch"     value={obs.git?.branch ?? "—"} mono />
            <DataRow label="Commit"         value={obs.git?.head?.slice(0, 7) ?? "—"} mono />
            <DataRow label="Skills"         value={skills > 0 ? `${skills}` : "—"} color={skills > 0 ? "var(--green)" : "var(--muted)"} />
            <DataRow label="Loop autonome"  value={loopRunning ? "active" : "inactive"} color={loopRunning ? "var(--green)" : "var(--muted)"} />
          </div>
          {(obs.git?.dirty?.length ?? 0) > 0 && (
            <div style={{ marginTop: 10, fontSize: 11, color: "var(--yellow)" }}>
              ⚠ Repo dirty — {obs.git!.dirty!.length} fichier{obs.git!.dirty!.length > 1 ? "s" : ""} modifié{obs.git!.dirty!.length > 1 ? "s" : ""}
            </div>
          )}
        </Card>
      </div>

      {/* ── Latences API (RÉEL mesurées server-side) ── */}
      <Card title={hasRealLatencies ? "Latences API HUB — RÉEL (mesurées)" : "Latences API HUB — indisponibles"}>
        {hasRealLatencies ? (
          <>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
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
                  {latencies.map((row) => (
                    <LatencyRow key={row.endpoint} row={row} />
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ padding: "6px 12px 0", fontSize: 11, color: "var(--border)" }}>
              Latences mesurées sur 5 appels server-side · p50 = médiane · p95 = max
            </div>
          </>
        ) : (
          <div style={{ padding: "16px 0", fontSize: 13, color: "var(--muted)" }}>
            Endpoint /api/performance indisponible — HUB non joignable
          </div>
        )}
      </Card>

      {/* ── Lighthouse (non configuré) ── */}
      <div style={{ marginTop: 20 }}>
        <SectionLabel>Sites — Lighthouse</SectionLabel>
        {lighthouseConfigured ? (
          // When lighthouse is eventually configured, real data will show here
          <div style={{ fontSize: 13, color: "var(--muted)" }}>Données disponibles</div>
        ) : (
          <InsetNotice
            icon="◳"
            text="Lighthouse non configuré"
            detail={
              perf
                ? "Le runtime /api/performance répond (capabilities.lighthouse_configured=false) — installer Lighthouse CLI pour activer les scores sites."
                : "Endpoint /api/performance indisponible."
            }
            variant="muted"
          />
        )}
      </div>

      <div style={{ marginTop: 16, fontSize: 11, color: "var(--border)" }}>
        Score santé, infra, latences API : RÉEL · Lighthouse : non configuré · Source : /api/observability + /api/performance
      </div>
    </div>
  );
}
