import { athosPost } from "@/lib/athos";

interface LoopStatus {
  running?: boolean;
  iterations?: number;
  idle_ticks?: number;
  last_event?: { type?: string; ts?: string } | null;
  policy?: {
    env_enabled?: boolean;
    default_tick?: number;
    skill_mutation_enabled?: boolean;
  };
}

interface LoopPayload {
  running?: boolean;
  iterations?: number;
  idle_ticks?: number;
  last_event?: LoopStatus["last_event"];
  policy?: LoopStatus["policy"];
  events?: { type?: string; ts?: string; data?: unknown }[];
}

interface TaskQueuePayload {
  tasks?: {
    id?: string;
    title?: string;
    status?: string;
    items?: { id?: string; label?: string; status?: string }[];
  }[];
  summary?: { total?: number; running?: number; done?: number; blocked?: number };
}

interface SkillPayload {
  skills?: { name?: string; description?: string; installed?: boolean; offline?: boolean }[];
}

const STATUS_COLOR: Record<string, string> = {
  running: "var(--green)",
  done: "var(--muted)",
  blocked: "var(--red)",
  pending: "var(--yellow)",
};

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

  return (
    <div style={{ maxWidth: 900 }}>
      <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 6 }}>Automations</h1>
      <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 24 }}>
        Boucle autonome · Task queue · Skills installés
      </p>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: 20,
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 11, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 16 }}>
          Boucle autonome
        </div>
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: loop.running ? "var(--green)" : "var(--border)",
                  boxShadow: loop.running ? "0 0 8px var(--green)" : "none",
                }}
              />
              <span style={{ fontSize: 15, fontWeight: 600, color: loop.running ? "var(--green)" : "var(--muted)" }}>
                {loop.running ? "En cours" : "Arrêtée"}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{loop.iterations ?? 0}</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>itérations</div>
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{loop.idle_ticks ?? 0}</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>idle ticks</div>
          </div>
          <div style={{ marginLeft: "auto", fontSize: 12, color: "var(--muted)" }}>
            Policy: env_enabled={loop.policy?.env_enabled ? "oui" : "non"}{" "}
            · tick={loop.policy?.default_tick ?? "—"}s
            {" "}· skill_mutation={loop.policy?.skill_mutation_enabled ? "oui" : "non"}
          </div>
        </div>
        {!loop.policy?.env_enabled && (
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--yellow)", background: "rgba(255,214,10,0.08)", padding: "8px 12px", borderRadius: 5 }}>
            ATHOS_AUTONOMOUS_LOOP_ENABLED=false · La boucle ne démarrera pas sans activation explicite
          </div>
        )}
      </div>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: 20,
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 11, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 16 }}>
          Task Queue
        </div>
        {taskList.length === 0 ? (
          <div style={{ color: "var(--muted)", fontSize: 13 }}>Aucune tâche en queue</div>
        ) : (
          taskList.map((task) => (
            <div key={task.id} style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{task.title ?? task.id}</span>
                <span
                  style={{
                    fontSize: 11,
                    color: STATUS_COLOR[task.status ?? ""] ?? "var(--muted)",
                    background: "var(--surface-2)",
                    padding: "2px 8px",
                    borderRadius: 4,
                  }}
                >
                  {task.status}
                </span>
              </div>
              {(task.items ?? []).map((item) => (
                <div
                  key={item.id}
                  style={{
                    fontSize: 12,
                    color: "var(--muted)",
                    padding: "4px 12px",
                    borderLeft: `2px solid ${STATUS_COLOR[item.status ?? ""] ?? "var(--border)"}`,
                    marginLeft: 8,
                    marginBottom: 3,
                  }}
                >
                  {item.label} · {item.status}
                </div>
              ))}
            </div>
          ))
        )}
      </div>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: 20,
        }}
      >
        <div style={{ fontSize: 11, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 16 }}>
          Skills ({installed.length} installés / {skills.length} déclarés)
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10 }}>
          {skills.map((skill) => (
            <div
              key={skill.name}
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 5,
                padding: "10px 12px",
                opacity: skill.installed ? 1 : 0.5,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{skill.name}</span>
                <span
                  style={{
                    fontSize: 9,
                    color: skill.installed ? "var(--green)" : "var(--muted)",
                    background: skill.installed ? "rgba(52,199,89,0.12)" : "var(--surface)",
                    padding: "1px 5px",
                    borderRadius: 3,
                  }}
                >
                  {skill.installed ? "ON" : "OFF"}
                </span>
              </div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>{skill.description}</div>
              {skill.offline && (
                <div style={{ fontSize: 10, color: "var(--blue)", marginTop: 4 }}>offline-ready</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
