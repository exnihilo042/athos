import { athosPost } from "@/lib/athos";

interface FailoverEvent {
  ts?: string;
  name?: string;
  label?: string;
  result?: string;
  engine?: string;
  context_hash?: string;
}

interface ObsPayload {
  failover?: FailoverEvent[];
  memory?: {
    ok?: boolean;
    missing?: string[];
    canonical_files?: { name: string; exists: boolean; size: number; updated_at?: string }[];
  };
  summary?: {
    failover_events?: number;
    memory_missing?: number;
    listening_ports?: number;
    loop_running?: boolean;
    attached_engines?: number;
    agent_processes?: number;
  };
  git?: { branch?: string; head?: string; dirty?: string[] };
  server_runtime?: { pid?: number; uptime_seconds?: number };
}

const LEVEL_COLOR: Record<string, string> = {
  failover: "var(--yellow)",
  error: "var(--red)",
  warn: "var(--yellow)",
  info: "var(--blue)",
};

function levelFromEvent(e: FailoverEvent): string {
  if (e.name === "failover") return "failover";
  if (e.result?.toLowerCase().includes("erreur") || e.result?.toLowerCase().includes("échec") || e.result?.toLowerCase().includes("error")) return "error";
  return "info";
}

function formatTs(ts?: string): string {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleString("fr-FR", {
      day: "2-digit", month: "2-digit", year: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, letterSpacing: 0.5, textTransform: "uppercase",
      padding: "2px 7px", borderRadius: 4,
      background: `color-mix(in srgb, ${color} 15%, transparent)`,
      color, border: `1px solid color-mix(in srgb, ${color} 30%, transparent)`,
      flexShrink: 0,
    }}>
      {label}
    </span>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "14px 16px" }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: color ?? "var(--text)", marginBottom: 4 }}>{value}</div>
      <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
    </div>
  );
}

export default async function AlertesPage() {
  let obs: ObsPayload = {};

  try {
    obs = await athosPost<ObsPayload>("/api/observability");
  } catch {}

  const events = (obs.failover ?? []).slice().reverse();
  const memOk = obs.memory?.ok ?? true;
  const missing = obs.memory?.missing ?? [];
  const hasAlerts = events.length > 0 || !memOk;

  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Alertes</h1>
        <p style={{ color: "var(--muted)", fontSize: 13, margin: 0 }}>
          Failovers, erreurs mémoire et anomalies système
        </p>
      </div>

      <div className="grid-auto-4" style={{ marginBottom: 24 }}>
        <StatCard
          label="Failovers"
          value={obs.summary?.failover_events ?? events.length}
          color={events.length > 0 ? "var(--yellow)" : "var(--green)"}
        />
        <StatCard
          label="Mémoire"
          value={memOk ? "OK" : `${missing.length} manquant${missing.length > 1 ? "s" : ""}`}
          color={memOk ? "var(--green)" : "var(--red)"}
        />
        <StatCard
          label="Ports actifs"
          value={obs.summary?.listening_ports ?? "—"}
        />
        <StatCard
          label="Engines attachés"
          value={obs.summary?.attached_engines ?? 0}
          color={(obs.summary?.attached_engines ?? 0) > 0 ? "var(--green)" : "var(--muted)"}
        />
      </div>

      {!memOk && missing.length > 0 && (
        <div style={{
          background: "rgba(255,69,58,0.08)", border: "1px solid rgba(255,69,58,0.25)",
          borderRadius: 8, padding: "14px 16px", marginBottom: 16,
          display: "flex", gap: 12, alignItems: "flex-start",
        }}>
          <span style={{ color: "var(--red)", fontSize: 14, flexShrink: 0, marginTop: 1 }}>⚠</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--red)", marginBottom: 4 }}>
              Fichiers mémoire manquants
            </div>
            <div style={{ fontSize: 12, color: "var(--muted)", display: "flex", flexWrap: "wrap", gap: 6 }}>
              {missing.map((f) => (
                <code key={f} style={{ background: "var(--surface-2)", padding: "1px 6px", borderRadius: 3 }}>{f}</code>
              ))}
            </div>
          </div>
        </div>
      )}

      {events.length === 0 && memOk ? (
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8,
          padding: "40px 24px", textAlign: "center",
        }}>
          <div style={{ fontSize: 24, marginBottom: 12 }}>◉</div>
          <div style={{ fontSize: 14, color: "var(--text)", marginBottom: 6 }}>Aucune alerte</div>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>Tous les systèmes opérationnels</div>
        </div>
      ) : (
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 11, letterSpacing: 1.2, color: "var(--muted)", textTransform: "uppercase", fontWeight: 600 }}>
              Événements récents
            </span>
            <span style={{ fontSize: 11, color: "var(--border)" }}>({events.length})</span>
          </div>

          {events.map((e, i) => {
            const level = levelFromEvent(e);
            const color = LEVEL_COLOR[level] ?? "var(--muted)";
            return (
              <div key={i} style={{
                padding: "14px 16px",
                borderBottom: i < events.length - 1 ? "1px solid var(--border)" : "none",
                display: "flex", gap: 14, alignItems: "flex-start",
              }}>
                <span style={{ color, fontSize: 10, marginTop: 3, flexShrink: 0 }}>●</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
                    <Badge label={level} color={color} />
                    {e.engine && (
                      <span style={{ fontSize: 11, color: "var(--muted)" }}>{e.engine}</span>
                    )}
                    {e.label && (
                      <span style={{ fontSize: 12, color: "var(--text)", fontWeight: 500 }}>{e.label}</span>
                    )}
                    <span style={{ fontSize: 11, color: "var(--border)", marginLeft: "auto" }}>
                      {formatTs(e.ts)}
                    </span>
                  </div>
                  {e.result && (
                    <div style={{
                      fontSize: 11, color: "var(--muted)",
                      background: "var(--surface-2)", borderRadius: 4,
                      padding: "6px 10px", fontFamily: "monospace",
                      whiteSpace: "pre-wrap", wordBreak: "break-word",
                      maxHeight: 80, overflow: "hidden",
                    }}>
                      {e.result.length > 300 ? e.result.slice(0, 300) + "…" : e.result}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {(obs.memory?.canonical_files?.length ?? 0) > 0 && (
        <div style={{ marginTop: 20, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
            <span style={{ fontSize: 11, letterSpacing: 1.2, color: "var(--muted)", textTransform: "uppercase", fontWeight: 600 }}>
              Fichiers mémoire
            </span>
          </div>
          <div style={{ padding: "4px 0" }}>
            {obs.memory!.canonical_files!.map((f) => (
              <div key={f.name} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "8px 16px", fontSize: 12,
              }}>
                <span style={{ color: f.exists ? "var(--green)" : "var(--red)", fontSize: 9 }}>●</span>
                <span style={{ flex: 1, fontFamily: "monospace", color: "var(--text)" }}>{f.name}</span>
                <span style={{ color: "var(--muted)" }}>{(f.size / 1024).toFixed(1)} KB</span>
                {f.updated_at && (
                  <span style={{ color: "var(--border)", fontSize: 11 }}>{formatTs(f.updated_at)}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
