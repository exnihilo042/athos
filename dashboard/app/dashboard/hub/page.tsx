import { athosPost } from "@/lib/athos";

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
    };
  };
  session?: {
    events?: number;
    exchanges?: number;
    actions?: number;
  };
  spend_policy?: {
    mode?: string;
    room_auto_respond?: boolean;
    room_auto_respond_engines?: string[];
  };
}

interface ObsPayload {
  git?: { head?: string; branch?: string; dirty?: unknown[] };
  server_runtime?: { pid?: number; uptime_seconds?: number };
  memory?: { ok?: boolean; missing?: string[] };
  summary?: {
    listening_ports?: number;
    launchd_jobs?: number;
    memory_missing?: number;
    failover_events?: number;
    installed_skills?: number;
    capability_graph_nodes?: number;
  };
  failover?: { ts?: string; label?: string; result?: string }[];
}

interface RespondersPayload {
  actors?: {
    claude?: { available?: boolean; last_problem?: { kind?: string; ts?: string } };
    codex?: { available?: boolean; last_problem?: { kind?: string; content?: string } };
  };
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: 20,
      }}
    >
      <div style={{ fontSize: 11, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 16 }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function Pill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "3px 10px",
        borderRadius: 20,
        fontSize: 12,
        background: ok ? "rgba(52,199,89,0.12)" : "rgba(255,69,58,0.12)",
        color: ok ? "var(--green)" : "var(--red)",
        border: `1px solid ${ok ? "rgba(52,199,89,0.25)" : "rgba(255,69,58,0.25)"}`,
      }}
    >
      <span style={{ fontSize: 8 }}>●</span>
      {label}
    </span>
  );
}

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
  const uptimeStr =
    uptime > 3600
      ? `${Math.floor(uptime / 3600)}h${Math.floor((uptime % 3600) / 60)}m`
      : `${Math.floor(uptime / 60)}m${Math.floor(uptime % 60)}s`;

  const graphSummary = status.capability_graph?.summary;
  const claudeOk = responders.actors?.claude?.available ?? false;
  const codexOk = responders.actors?.codex?.available ?? false;

  return (
    <div style={{ maxWidth: 1100 }}>
      <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 6 }}>Vue Centrale</h1>
      <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 24 }}>
        État temps réel — rafraîchi à chaque chargement
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 24 }}>
        <Card title="Moteur">
          <div style={{ fontSize: 20, fontWeight: 700, color: "var(--accent)", marginBottom: 8 }}>
            {status.engine ?? "—"}
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Pill ok={!status.degraded} label={status.degraded ? "dégradé" : "opérationnel"} />
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
            Disponibles : {(status.available ?? []).join(", ") || "—"}
          </div>
          <div style={{ marginTop: 4, fontSize: 12, color: "var(--muted)" }}>
            Politique : {status.spend_policy?.mode ?? "—"}
          </div>
        </Card>

        <Card title="Responders Room">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13 }}>claude</span>
              <Pill ok={claudeOk} label={claudeOk ? "disponible" : responders.actors?.claude?.last_problem?.kind ?? "bloqué"} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13 }}>codex</span>
              <Pill ok={codexOk} label={codexOk ? "disponible" : responders.actors?.codex?.last_problem?.kind ?? "bloqué"} />
            </div>
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
            Auto-respond: {status.spend_policy?.room_auto_respond ? "activé" : "désactivé"}
            {" · "}engines: {(status.spend_policy?.room_auto_respond_engines ?? []).join(", ") || "—"}
          </div>
        </Card>

        <Card title="Budget">
          <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
            {status.budget !== undefined ? `${status.budget.toFixed(4)} €` : "—"}
          </div>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>Zéro dépense API par défaut</div>
        </Card>

        <Card title="Session">
          <div style={{ display: "flex", gap: 20 }}>
            {[
              { label: "Events", value: status.session?.events },
              { label: "Échanges", value: status.session?.exchanges },
              { label: "Actions", value: status.session?.actions },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{value ?? "—"}</div>
                <div style={{ fontSize: 11, color: "var(--muted)" }}>{label}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 24 }}>
        <Card title="Capability Graph">
          {graphSummary ? (
            <>
              <div style={{ display: "flex", gap: 20, marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>{graphSummary.available_nodes}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>disponibles</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700 }}>{graphSummary.nodes}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>total nœuds</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700 }}>{graphSummary.edges}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>edges</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700 }}>{graphSummary.offline_ready_nodes}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>offline-ready</div>
                </div>
              </div>
              <Pill ok={graphSummary.austere_mode_ready ?? false} label={graphSummary.austere_mode_ready ? "austere mode OK" : "austere mode KO"} />
            </>
          ) : (
            <span style={{ color: "var(--muted)" }}>—</span>
          )}
        </Card>

        <Card title="Infra">
          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
            {[
              { label: ":7474 ATHOS HUB", ok: true, detail: `PID ${obs.server_runtime?.pid ?? "—"} · uptime ${uptimeStr}` },
              { label: ":8765 agentmemory", ok: (obs.summary?.listening_ports ?? 0) > 0, detail: "Python" },
              { label: ":20128 9router", ok: (obs.summary?.listening_ports ?? 0) > 0, detail: "Next.js" },
            ].map(({ label, ok, detail }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: ok ? "var(--green)" : "var(--red)", fontSize: 10 }}>●</span>
                <span style={{ flex: 1 }}>{label}</span>
                <span style={{ color: "var(--muted)", fontSize: 11 }}>{detail}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
            Git: {obs.git?.branch ?? "—"} @ {obs.git?.head?.slice(0, 7) ?? "—"}
            {(obs.git?.dirty?.length ?? 0) > 0 && (
              <span style={{ color: "var(--yellow)" }}> · dirty</span>
            )}
          </div>
        </Card>

        <Card title="Mémoire">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Pill ok={obs.memory?.ok ?? false} label={obs.memory?.ok ? "OK" : "fichiers manquants"} />
          </div>
          {(obs.memory?.missing?.length ?? 0) > 0 && (
            <div style={{ fontSize: 12, color: "var(--red)" }}>
              Manquants: {obs.memory?.missing?.join(", ")}
            </div>
          )}
          <div style={{ fontSize: 12, color: "var(--muted)" }}>
            Ports: {obs.summary?.listening_ports ?? "—"} ·{" "}
            Launchd: {obs.summary?.launchd_jobs ?? "—"} ·{" "}
            Skills: {obs.summary?.installed_skills ?? "—"}
          </div>
        </Card>
      </div>

      {(obs.failover?.length ?? 0) > 0 && (
        <Card title="Failover récents">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {(obs.failover ?? []).slice(-4).map((f, i) => (
              <div key={i} style={{ display: "flex", gap: 12, fontSize: 12 }}>
                <span style={{ color: "var(--muted)", minWidth: 160 }}>
                  {f.ts ? new Date(f.ts).toLocaleString("fr-FR") : "—"}
                </span>
                <span style={{ color: "var(--yellow)" }}>{f.label}</span>
                <span style={{ color: "var(--muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {f.result}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
