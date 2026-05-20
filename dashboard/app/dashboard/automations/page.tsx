import { athosPost } from "@/lib/athos";
import { Card, StatCard, Badge, SectionLabel, PageHeader, DataRow } from "@/components/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

interface LoopPayload {
  running?: boolean;
  iterations?: number;
  idle_ticks?: number;
  last_event?: { type?: string; ts?: string; data?: unknown } | null;
  policy?: {
    env_enabled?: boolean;
    default_tick?: number;
    skill_mutation_enabled?: boolean;
  };
  events?: { type?: string; ts?: string; data?: unknown }[];
}

interface TaskQueuePayload {
  tasks?: {
    id?: string;
    title?: string;
    status?: string;
    items?: { id?: string; label?: string; status?: string }[];
  }[];
  summary?: { total?: number; running?: number; done?: number; blocked?: number; pending?: number };
}

interface SkillPayload {
  skills?: { name?: string; description?: string; installed?: boolean; offline?: boolean }[];
}

// ── Visual config ─────────────────────────────────────────────────────────────

const TASK_STATUS_CONFIG: Record<string, { color: string; variant: "green" | "red" | "yellow" | "blue" | "muted" | "border" }> = {
  running: { color: "var(--green)",  variant: "green" },
  done:    { color: "var(--muted)",  variant: "muted" },
  blocked: { color: "var(--red)",    variant: "red" },
  failed:  { color: "var(--red)",    variant: "red" },
  pending: { color: "var(--yellow)", variant: "yellow" },
};

function formatTs(ts?: string): string {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch { return ts; }
}

// ── Codex pending zone ────────────────────────────────────────────────────────

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
      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)" }}>{label}</div>
        <div style={{ fontSize: 11, color: "var(--border)", marginTop: 2 }}>{detail}</div>
      </div>
      <Badge label="CODEX" variant="muted" />
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AutomationsPage() {
  let loop: LoopPayload = {};
  let tasks: TaskQueuePayload = {};
  let skillData: SkillPayload = {};

  try {
    [loop, tasks, skillData] = await Promise.all([
      athosPost<LoopPayload>("/api/loop"),
      athosPost<TaskQueuePayload>("/api/conversation", { action: "health" }),
      athosPost<SkillPayload>("/api/skills"),
    ]);
  } catch {}

  const taskList = tasks.tasks ?? [];
  const skills = skillData.skills ?? [];
  const installed = skills.filter((s) => s.installed);
  const offline = skills.filter((s) => s.offline);
  const taskSummary = tasks.summary ?? {};

  const loopEnabled = loop.policy?.env_enabled ?? false;

  return (
    <div style={{ maxWidth: 1000 }}>
      <PageHeader
        title="Automations"
        subtitle="Boucle autonome · Task queue · Skills ATHOS"
      />

      {/* ── KPI ── */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Boucle autonome"
          value={loop.running ? "Active" : "Inactive"}
          sub={loopEnabled ? `tick ${loop.policy?.default_tick ?? "—"}s` : "désactivée par env"}
          color={loop.running ? "var(--green)" : "var(--muted)"}
          size="lg"
        />
        <StatCard
          label="Itérations"
          value={loop.iterations ?? 0}
          sub="depuis démarrage"
          color="var(--text)"
        />
        <StatCard
          label="Skills installés"
          value={installed.length}
          sub={`${offline.length} offline-ready`}
          color={installed.length > 0 ? "var(--green)" : "var(--muted)"}
        />
        <StatCard
          label="Tâches queue"
          value={taskSummary.total ?? taskList.length}
          sub={taskSummary.running ? `${taskSummary.running} en cours` : "queue vide"}
          color={taskSummary.running ? "var(--accent)" : "var(--muted)"}
        />
      </div>

      {/* ── Boucle autonome ── */}
      <Card title="Boucle autonome — RÉEL">
        <div style={{ display: "flex", gap: 24, alignItems: "flex-start", flexWrap: "wrap", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: loop.running ? "var(--green)" : "var(--border)",
                boxShadow: loop.running ? "0 0 8px var(--green)" : "none",
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: 15, fontWeight: 600, color: loop.running ? "var(--green)" : "var(--muted)" }}>
              {loop.running ? "En cours" : "Arrêtée"}
            </span>
          </div>
          {loop.last_event && (
            <div style={{ fontSize: 12, color: "var(--muted)" }}>
              Dernier event: <span style={{ color: "var(--text)" }}>{(loop.last_event as { type?: string }).type ?? "—"}</span>
              {" · "}{formatTs((loop.last_event as { ts?: string }).ts)}
            </div>
          )}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 16 }}>
          <DataRow label="env_enabled"         value={loopEnabled ? "oui" : "non"}  color={loopEnabled ? "var(--green)" : "var(--red)"}   mono />
          <DataRow label="tick"                 value={`${loop.policy?.default_tick ?? "—"}s`} mono />
          <DataRow label="skill_mutation"       value={loop.policy?.skill_mutation_enabled ? "oui" : "non"} mono />
          <DataRow label="idle_ticks"           value={loop.idle_ticks ?? 0} />
        </div>

        {!loopEnabled && (
          <div
            style={{
              background: "rgba(255,214,10,0.08)",
              border: "1px solid rgba(255,214,10,0.25)",
              borderRadius: 5,
              padding: "8px 14px",
              fontSize: 12,
              color: "var(--yellow)",
            }}
          >
            ⚠ <strong>ATHOS_AUTONOMOUS_LOOP_ENABLED=false</strong> — La boucle ne démarrera pas tant que cette variable n'est pas activée dans le .env
          </div>
        )}

        <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8, letterSpacing: 0.5 }}>CONTRÔLES — en attente Codex</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["Démarrer", "Arrêter", "Pause", "Reset compteurs"].map((label) => (
              <button
                key={label}
                disabled
                style={{
                  fontSize: 11,
                  padding: "5px 12px",
                  borderRadius: 5,
                  border: "1px dashed var(--border)",
                  background: "none",
                  color: "var(--border)",
                  cursor: "not-allowed",
                }}
              >
                {label}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 6, fontSize: 10, color: "var(--border)" }}>
            Requiert endpoint /api/autonomous_loop {"{"}action: start|stop{"}"} — scope Codex
          </div>
        </div>
      </Card>

      {/* ── Task queue ── */}
      <div style={{ marginTop: 20, marginBottom: 20 }}>
        <SectionLabel count={taskList.length}>Task Queue — RÉEL</SectionLabel>
        {taskList.length === 0 ? (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "32px 24px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 20, color: "var(--border)", marginBottom: 8 }}>◱</div>
            <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 4 }}>Queue vide</div>
            <div style={{ fontSize: 11, color: "var(--border)" }}>Aucune tâche en cours · Les tâches apparaissent quand ATHOS travaille</div>
          </div>
        ) : (
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
            {taskList.map((task, i) => {
              const sc = TASK_STATUS_CONFIG[task.status ?? ""] ?? TASK_STATUS_CONFIG.pending;
              return (
                <div
                  key={task.id ?? i}
                  style={{
                    padding: "12px 16px",
                    borderBottom: i < taskList.length - 1 ? "1px solid var(--border)" : "none",
                    borderLeft: `3px solid ${sc.color}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, gap: 8, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{task.title ?? task.id}</span>
                    <Badge label={task.status ?? "—"} variant={sc.variant} />
                  </div>
                  {(task.items ?? []).map((item) => {
                    const isc = TASK_STATUS_CONFIG[item.status ?? ""] ?? TASK_STATUS_CONFIG.pending;
                    return (
                      <div
                        key={item.id}
                        style={{
                          fontSize: 11,
                          color: "var(--muted)",
                          padding: "3px 0 3px 12px",
                          borderLeft: `2px solid ${isc.color}`,
                          marginLeft: 8,
                          marginBottom: 2,
                          display: "flex",
                          justifyContent: "space-between",
                        }}
                      >
                        <span>{item.label}</span>
                        <span style={{ color: isc.color, fontSize: 10 }}>{item.status}</span>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        )}

        <div style={{ marginTop: 12 }}>
          <CodexPendingZone
            label="Contrôles tâches : pause / retry / cancel / resume"
            detail="Endpoint /api/tasks {action, task_id} — Codex doit valider les transitions d'état"
          />
        </div>
      </div>

      {/* ── Skills ── */}
      <div>
        <SectionLabel count={skills.length}>
          Skills — {installed.length} installés · {offline.length} offline-ready
        </SectionLabel>
        {skills.length === 0 ? (
          <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "24px", textAlign: "center", color: "var(--muted)", fontSize: 13 }}>
            Aucun skill déclaré — endpoint /api/skills non disponible
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))", gap: 8 }}>
            {skills.map((skill) => (
              <div
                key={skill.name}
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${skill.installed ? "var(--green)" : "var(--border)"}`,
                  borderRadius: 6,
                  padding: "10px 12px",
                  opacity: skill.installed ? 1 : 0.55,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6, gap: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>{skill.name}</span>
                  <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                    <Badge label={skill.installed ? "ON" : "OFF"} variant={skill.installed ? "green" : "border"} />
                    {skill.offline && <Badge label="offline" variant="blue" />}
                  </div>
                </div>
                {skill.description && (
                  <div style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.4 }}>{skill.description}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
