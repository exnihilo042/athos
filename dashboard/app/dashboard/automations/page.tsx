import { athosPost } from "@/lib/athos";
import { Card, StatCard, SectionLabel, PageHeader } from "@/components/ui";
import Link from "next/link";
import AutomationControlsClient from "@/components/AutomationControlsClient";
import type { AutonomousLoopPayload, BackendTask, BackendTaskSummary } from "@/lib/types";

// ── Types (local, subset) ─────────────────────────────────────────────────────

interface SkillPayload {
  skills?: { name?: string; description?: string; installed?: boolean; offline?: boolean }[];
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function AutomationsPage() {
  let loop: AutonomousLoopPayload = {
    running: false,
    iterations: 0,
    idle_ticks: 0,
    policy: { env_enabled: false, default_tick: 60, skill_mutation_enabled: false },
    last_event: null,
  };
  let taskList: BackendTask[] = [];
  let taskSummary: BackendTaskSummary = { total: 0, active: 0, counts: {}, recent: [] };
  let skillData: SkillPayload = {};

  try {
    const [loopData, tasksData, skills] = await Promise.all([
      athosPost<AutonomousLoopPayload>("/api/autonomous_loop", { action: "status" }),
      athosPost<{ ok: boolean; tasks: BackendTask[]; summary: BackendTaskSummary }>(
        "/api/tasks",
        { action: "list", limit: 50 }
      ),
      athosPost<SkillPayload>("/api/skills").catch(() => ({ skills: [] })),
    ]);
    loop = loopData;
    taskList = tasksData.tasks ?? [];
    taskSummary = tasksData.summary ?? taskSummary;
    skillData = skills;
  } catch {
    // HUB indisponible — render avec valeurs vides
  }

  const skills = skillData.skills ?? [];
  const installed = skills.filter((s) => s.installed);
  const offline = skills.filter((s) => s.offline);

  const counts = taskSummary.counts ?? {};
  const activeTaskCount = (counts.queued ?? 0) + (counts.running ?? 0) + (counts.paused ?? 0) + (counts.blocked ?? 0);

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
          sub={loop.policy?.env_enabled ? `tick ${loop.policy?.default_tick ?? "—"}s` : "désactivée par env"}
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
          label="Tâches actives"
          value={activeTaskCount}
          sub={taskSummary.total > 0 ? `${taskSummary.total} total queue` : "queue vide"}
          color={activeTaskCount > 0 ? "var(--accent)" : "var(--muted)"}
        />
      </div>

      {/* ── Contrôles interactifs (client) ── */}
      <AutomationControlsClient
        initialLoop={loop}
        initialTasks={taskList}
        initialSummary={counts as Record<string, number>}
      />

      {/* ── Skills runtime ── */}
      <div style={{ marginTop: 24 }}>
        <SectionLabel count={skills.length}>
          Skills runtime — {installed.length} installés · {offline.length} offline-ready
          {" "}
          <Link href="/dashboard/skills" style={{ fontSize: 10, color: "var(--accent)", textDecoration: "none", marginLeft: 8 }}>
            Voir catalogue complet →
          </Link>
        </SectionLabel>
        {skills.length === 0 ? (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "24px",
              textAlign: "center",
              color: "var(--muted)",
              fontSize: 13,
            }}
          >
            Endpoint /api/skills non disponible — catalogue local disponible sur{" "}
            <Link href="/dashboard/skills" style={{ color: "var(--accent)" }}>
              /dashboard/skills
            </Link>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))",
              gap: 8,
            }}
          >
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
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: 6,
                    gap: 8,
                  }}
                >
                  <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>
                    {skill.name}
                  </span>
                  <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                    <span
                      style={{
                        fontSize: 9,
                        padding: "1px 6px",
                        borderRadius: 20,
                        background: skill.installed
                          ? "rgba(52,199,89,0.14)"
                          : "transparent",
                        color: skill.installed ? "var(--green)" : "var(--border)",
                        border: `1px solid ${skill.installed ? "rgba(52,199,89,0.28)" : "var(--border)"}`,
                        fontWeight: 600,
                      }}
                    >
                      {skill.installed ? "ON" : "OFF"}
                    </span>
                    {skill.offline && (
                      <span
                        style={{
                          fontSize: 9,
                          padding: "1px 6px",
                          borderRadius: 20,
                          background: "rgba(74,158,255,0.14)",
                          color: "var(--blue)",
                          border: "1px solid rgba(74,158,255,0.28)",
                          fontWeight: 600,
                        }}
                      >
                        offline
                      </span>
                    )}
                  </div>
                </div>
                {skill.description && (
                  <div style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.4 }}>
                    {skill.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
