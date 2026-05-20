import { athosPost } from "@/lib/athos";
import { Card, StatCard, Badge, SectionLabel, PageHeader, DataRow } from "@/components/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ReportPayload {
  brief?: string;
  date?: string;
  sections?: { title?: string; content?: string }[];
  summary?: { total_sessions?: number; total_messages?: number; failovers?: number; actions?: number };
}

interface SessionPayload {
  summary?: { total?: number; running?: number; done?: number; blocked?: number; pending?: number };
  active_sessions?: number;
  total_messages?: number;
}

interface LoopPayload {
  running?: boolean;
  iterations?: number;
  events?: { type?: string; ts?: string; data?: unknown }[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTs(ts?: string): string {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch { return ts; }
}

function CodexPendingZone({ label, detail }: { label: string; detail: string }) {
  return (
    <div
      style={{
        border: "1px dashed var(--border)",
        borderRadius: 6,
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        opacity: 0.6,
      }}
    >
      <span style={{ fontSize: 14, color: "var(--border)" }}>◱</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)" }}>{label}</div>
        <div style={{ fontSize: 11, color: "var(--border)", marginTop: 2 }}>{detail}</div>
      </div>
      <Badge label="CODEX" variant="muted" />
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function ReportsPage() {
  let report: ReportPayload = {};
  let session: SessionPayload = {};
  let loop: LoopPayload = {};

  try {
    [report, session, loop] = await Promise.all([
      athosPost<ReportPayload>("/api/report", { type: "daily" }),
      athosPost<SessionPayload>("/api/conversation", { action: "health" }),
      athosPost<LoopPayload>("/api/loop"),
    ]);
  } catch {}

  const loopEvents = loop.events ?? [];
  const failoverEvents = loopEvents.filter((e) => e.type === "failover");
  const hasBrief = !!(report.brief);

  return (
    <div style={{ maxWidth: 1000 }}>
      <PageHeader
        title="Rapports"
        subtitle="Daily brief · Récapitulatif session · Synthèse système · Failovers"
      />

      {/* ── KPIs ── */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Daily brief"
          value={hasBrief ? "Disponible" : "En attente"}
          sub={report.date ? formatTs(report.date) : "pas de date"}
          color={hasBrief ? "var(--green)" : "var(--muted)"}
          size="lg"
        />
        <StatCard
          label="Messages session"
          value={session.total_messages ?? "—"}
          sub={session.active_sessions ? `${session.active_sessions} session(s)` : "sessions inconnues"}
          color="var(--text)"
        />
        <StatCard
          label="Failovers"
          value={failoverEvents.length}
          sub={failoverEvents.length > 0 ? "incidents détectés" : "aucun incident"}
          color={failoverEvents.length > 0 ? "var(--red)" : "var(--green)"}
        />
        <StatCard
          label="Itérations boucle"
          value={loop.iterations ?? 0}
          sub={loop.running ? "boucle active" : "boucle arrêtée"}
          color={loop.running ? "var(--accent)" : "var(--muted)"}
        />
      </div>

      {/* ── Daily brief ── */}
      <Card title="Daily Brief — RÉEL">
        {hasBrief ? (
          <>
            {report.date && (
              <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 14, letterSpacing: 0.5 }}>
                Généré le {formatTs(report.date)}
              </div>
            )}
            <pre
              style={{
                fontSize: 13,
                color: "var(--text)",
                whiteSpace: "pre-wrap",
                lineHeight: 1.65,
                fontFamily: "var(--font-mono, monospace)",
                margin: 0,
              }}
            >
              {report.brief}
            </pre>
            {(report.sections ?? []).length > 0 && (
              <div style={{ marginTop: 20, borderTop: "1px solid var(--border)", paddingTop: 16 }}>
                {(report.sections ?? []).map((s, i) => (
                  <div key={i} style={{ marginBottom: 16 }}>
                    {s.title && (
                      <div
                        style={{
                          fontSize: 11,
                          letterSpacing: 1,
                          color: "var(--accent)",
                          textTransform: "uppercase",
                          fontWeight: 600,
                          marginBottom: 8,
                        }}
                      >
                        {s.title}
                      </div>
                    )}
                    <pre
                      style={{
                        fontSize: 12,
                        color: "var(--muted)",
                        whiteSpace: "pre-wrap",
                        lineHeight: 1.6,
                        margin: 0,
                      }}
                    >
                      {s.content}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
              <span style={{ fontSize: 20, color: "var(--border)" }}>◱</span>
              <div>
                <div style={{ fontSize: 13, color: "var(--muted)" }}>Brief non disponible</div>
                <div style={{ fontSize: 11, color: "var(--border)", marginTop: 2 }}>
                  L'endpoint /api/report répond vide — ATHOS n'a pas encore généré de rapport aujourd'hui.
                </div>
              </div>
            </div>
            <div
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 5,
                padding: "10px 14px",
                fontSize: 12,
                fontFamily: "monospace",
                color: "var(--muted)",
              }}
            >
              POST /api/report {"{"}"type": "daily"{"}"} → {"{"}"brief": "...", "date": "..."{"}"}
            </div>
          </div>
        )}
      </Card>

      {/* ── Session recap ── */}
      <div style={{ marginTop: 20 }}>
        <Card title="Récapitulatif Session — RÉEL">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
            <DataRow label="Sessions actives"  value={session.active_sessions ?? "—"} />
            <DataRow label="Messages totaux"   value={session.total_messages ?? "—"} />
            <DataRow label="Tâches total"      value={session.summary?.total ?? "—"} />
            <DataRow label="En cours"          value={session.summary?.running ?? "—"} color={session.summary?.running ? "var(--accent)" : undefined} />
            <DataRow label="Terminées"         value={session.summary?.done ?? "—"} color="var(--green)" />
            <DataRow label="Bloquées"          value={session.summary?.blocked ?? "—"} color={session.summary?.blocked ? "var(--red)" : undefined} />
          </div>
          {!session.summary && !session.total_messages && (
            <div style={{ marginTop: 12, fontSize: 11, color: "var(--border)" }}>
              Endpoint /api/conversation {"{"}"action": "health"{"}"} — réponse vide ou schéma non supporté
            </div>
          )}
        </Card>
      </div>

      {/* ── Failovers ── */}
      <div style={{ marginTop: 20 }}>
        <SectionLabel count={failoverEvents.length}>Failovers — RÉEL</SectionLabel>
        {failoverEvents.length === 0 ? (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "28px 24px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 18, color: "var(--green)", marginBottom: 8 }}>✓</div>
            <div style={{ fontSize: 13, color: "var(--muted)" }}>Aucun failover enregistré</div>
            <div style={{ fontSize: 11, color: "var(--border)", marginTop: 4 }}>
              {loopEvents.length > 0
                ? `${loopEvents.length} événement(s) boucle · zéro failover`
                : "Loop events non disponibles — /api/loop"}
            </div>
          </div>
        ) : (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              overflow: "hidden",
            }}
          >
            {failoverEvents.map((ev, i) => (
              <div
                key={i}
                style={{
                  padding: "10px 16px",
                  borderBottom: i < failoverEvents.length - 1 ? "1px solid var(--border)" : "none",
                  borderLeft: "3px solid var(--red)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ fontSize: 13, color: "var(--text)", fontWeight: 500 }}>{ev.type}</div>
                  {Boolean(ev.data) && (
                    <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
                      {JSON.stringify(ev.data).slice(0, 120)}
                    </div>
                  )}
                </div>
                <span style={{ fontSize: 11, color: "var(--muted)", whiteSpace: "nowrap" }}>
                  {formatTs(ev.ts)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Loop events feed ── */}
      {loopEvents.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <SectionLabel count={loopEvents.length}>Événements boucle récents — RÉEL</SectionLabel>
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              overflow: "hidden",
            }}
          >
            {loopEvents.slice(0, 12).map((ev, i) => {
              const isFailover = ev.type === "failover";
              const shown = Math.min(loopEvents.length, 12);
              return (
                <div
                  key={i}
                  style={{
                    padding: "7px 16px",
                    borderBottom: i < shown - 1 ? "1px solid var(--border)" : "none",
                    borderLeft: `3px solid ${isFailover ? "var(--red)" : "var(--border)"}`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <span
                    style={{
                      fontSize: 12,
                      color: isFailover ? "var(--red)" : "var(--muted)",
                      fontFamily: "monospace",
                    }}
                  >
                    {ev.type ?? "—"}
                  </span>
                  <span style={{ fontSize: 11, color: "var(--border)" }}>{formatTs(ev.ts)}</span>
                </div>
              );
            })}
          </div>
          {loopEvents.length > 12 && (
            <div style={{ fontSize: 11, color: "var(--border)", marginTop: 6, textAlign: "right" }}>
              + {loopEvents.length - 12} événements antérieurs non affichés
            </div>
          )}
        </div>
      )}

      {/* ── CODEX-pending sections ── */}
      <div style={{ marginTop: 24 }}>
        <SectionLabel>Sections en attente backend — CODEX</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <CodexPendingZone
            label="Rapport actions ATHOS"
            detail="Endpoint /api/report {type: 'actions'} — liste des actions autonomes exécutées par session"
          />
          <CodexPendingZone
            label="Synthèse hebdomadaire"
            detail="Endpoint /api/report {type: 'weekly'} — agrégat 7 jours : sessions, coûts, failovers, uptime"
          />
          <CodexPendingZone
            label="Rapport coûts API"
            detail="Endpoint /api/report {type: 'costs'} — budget consommé par moteur, par jour"
          />
          <CodexPendingZone
            label="Export JSON / markdown"
            detail="Endpoint /api/report {type: 'export', format: 'md|json'} — téléchargement rapport complet"
          />
        </div>
      </div>
    </div>
  );
}
