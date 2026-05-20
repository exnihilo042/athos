"use client";

import { useState, useEffect, useCallback } from "react";
import type { AutonomousLoopPayload, BackendTask, BackendTaskStatus } from "@/lib/types";

// ── Proxy helper ───────────────────────────────────────────────────────────────
// Client-side calls must go through /api/athos-proxy (Next.js → HUB :7474)

async function proxyPost<T = unknown>(
  endpoint: string,
  payload: Record<string, unknown> = {}
): Promise<T> {
  const res = await fetch("/api/athos-proxy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint, payload }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`proxy ${endpoint} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Status label helpers ───────────────────────────────────────────────────────

const TASK_COLORS: Record<BackendTaskStatus | string, string> = {
  queued:    "var(--yellow)",
  running:   "var(--green)",
  paused:    "var(--blue)",
  blocked:   "var(--red)",
  completed: "var(--muted)",
  failed:    "var(--red)",
  cancelled: "var(--border)",
  stale:     "var(--border)",
};

const TASK_LABELS: Record<BackendTaskStatus | string, string> = {
  queued: "En attente", running: "En cours", paused: "Pausée",
  blocked: "Bloquée", completed: "Terminée", failed: "Échouée",
  cancelled: "Annulée", stale: "Périmée",
};

function formatTs(ts?: string): string {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleString("fr-FR", {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
    });
  } catch { return ts; }
}

// ── Loop controls ──────────────────────────────────────────────────────────────

function LoopControls({
  loop,
  onAction,
  loading,
}: {
  loop: AutonomousLoopPayload;
  onAction: (action: string) => Promise<void>;
  loading: boolean;
}) {
  const running = loop.running;
  const enabled = loop.policy?.env_enabled ?? false;

  const controls: { label: string; action: string; disabled?: boolean }[] = [
    { label: "Démarrer",        action: "start",  disabled: running || !enabled },
    { label: "Arrêter",         action: "stop",   disabled: !running },
    { label: "Pause",           action: "pause",  disabled: !running },
    { label: "Reset compteurs", action: "reset",  disabled: false },
  ];

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: running ? "var(--green)" : "var(--border)",
            boxShadow: running ? "0 0 8px var(--green)" : "none",
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontSize: 15,
            fontWeight: 600,
            color: running ? "var(--green)" : "var(--muted)",
          }}
        >
          {running ? "En cours" : "Arrêtée"}
        </span>
        {loop.last_event && (
          <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 8 }}>
            Dernier event:{" "}
            <span style={{ color: "var(--text)" }}>
              {(loop.last_event as { type?: string }).type ?? "—"}
            </span>
            {" · "}
            {formatTs((loop.last_event as { ts?: string }).ts)}
          </span>
        )}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
          gap: 8,
          marginBottom: 12,
          fontSize: 12,
          color: "var(--muted)",
        }}
      >
        {[
          { label: "env_enabled",    value: enabled ? "oui" : "non",      color: enabled ? "var(--green)" : "var(--red)" },
          { label: "tick",           value: `${loop.policy?.default_tick ?? "—"}s` },
          { label: "skill_mutation", value: loop.policy?.skill_mutation_enabled ? "oui" : "non" },
          { label: "idle_ticks",     value: String(loop.idle_ticks ?? 0) },
          { label: "itérations",     value: String(loop.iterations ?? 0) },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "5px 0",
              borderBottom: "1px solid var(--border)",
              fontSize: 12,
            }}
          >
            <span style={{ color: "var(--muted)" }}>{label}</span>
            <span
              style={{
                color: color ?? "var(--text)",
                fontFamily: "monospace",
                fontWeight: 500,
              }}
            >
              {value}
            </span>
          </div>
        ))}
      </div>

      {!enabled && (
        <div
          style={{
            background: "rgba(255,214,10,0.08)",
            border: "1px solid rgba(255,214,10,0.25)",
            borderRadius: 5,
            padding: "7px 12px",
            fontSize: 11,
            color: "var(--yellow)",
            marginBottom: 12,
          }}
        >
          ⚠ <strong>ATHOS_AUTONOMOUS_LOOP_ENABLED=false</strong> — démarrage impossible
        </div>
      )}

      <div
        style={{
          paddingTop: 12,
          borderTop: "1px solid var(--border)",
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontSize: 10,
            letterSpacing: 1,
            color: "var(--muted)",
            textTransform: "uppercase",
            marginRight: 4,
          }}
        >
          Contrôles
        </span>
        {controls.map(({ label, action, disabled }) => (
          <button
            key={action}
            disabled={disabled || loading}
            onClick={() => onAction(action)}
            style={{
              fontSize: 11,
              padding: "5px 12px",
              borderRadius: 5,
              border: `1px solid ${disabled ? "var(--border)" : "var(--accent)"}`,
              background: disabled ? "none" : "rgba(120,60,255,0.08)",
              color: disabled ? "var(--border)" : "var(--accent)",
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: loading ? 0.5 : 1,
              transition: "opacity 0.15s",
            }}
          >
            {label}
          </button>
        ))}
        {loading && (
          <span style={{ fontSize: 11, color: "var(--muted)" }}>…</span>
        )}
      </div>
    </div>
  );
}

// ── Task list ──────────────────────────────────────────────────────────────────

function TaskRow({
  task,
  onAction,
  loading,
}: {
  task: BackendTask;
  onAction: (taskId: string, action: string) => Promise<void>;
  loading: boolean;
}) {
  const color = TASK_COLORS[task.status] ?? "var(--muted)";
  const label = TASK_LABELS[task.status] ?? task.status;

  const actions = [
    { label: "Pause",    action: "pause",  show: task.status === "running" },
    { label: "Reprendre",action: "resume", show: task.status === "paused" || task.status === "blocked" },
    { label: "Retry",    action: "retry",  show: task.status === "failed" || task.status === "blocked" },
    { label: "Annuler",  action: "cancel", show: !["completed","cancelled","stale"].includes(task.status) },
  ].filter((a) => a.show);

  return (
    <div
      style={{
        padding: "11px 16px",
        borderLeft: `3px solid ${color}`,
        display: "grid",
        gridTemplateColumns: "1fr auto",
        gap: 12,
        alignItems: "flex-start",
      }}
    >
      <div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 4,
          }}
        >
          <span
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "var(--text)",
            }}
          >
            {task.title}
          </span>
          <span
            style={{
              fontSize: 10,
              padding: "1px 7px",
              borderRadius: 20,
              background: `color-mix(in srgb, ${color} 14%, transparent)`,
              color,
              border: `1px solid color-mix(in srgb, ${color} 28%, transparent)`,
              fontWeight: 600,
              whiteSpace: "nowrap",
            }}
          >
            {label}
          </span>
          {task.source && (
            <span
              style={{ fontSize: 10, color: "var(--border)", fontFamily: "monospace" }}
            >
              {task.source}
            </span>
          )}
        </div>
        <div style={{ fontSize: 11, color: "var(--muted)" }}>
          {task.blocked_reason
            ? <span style={{ color: "var(--red)" }}>⛔ {task.blocked_reason}</span>
            : task.content
            ? task.content.slice(0, 100) + (task.content.length > 100 ? "…" : "")
            : null}
        </div>
        <div
          style={{
            fontSize: 10,
            color: "var(--border)",
            marginTop: 4,
            fontFamily: "monospace",
          }}
        >
          {task.task_id.slice(0, 22)}
          {task.updated_at && ` · ${formatTs(task.updated_at)}`}
        </div>
      </div>
      {actions.length > 0 && (
        <div style={{ display: "flex", gap: 5, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {actions.map(({ label: btnLabel, action }) => (
            <button
              key={action}
              disabled={loading}
              onClick={() => onAction(task.task_id, action)}
              style={{
                fontSize: 10,
                padding: "3px 9px",
                borderRadius: 4,
                border: "1px solid var(--border)",
                background: "none",
                color: action === "cancel" ? "var(--red)" : "var(--muted)",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.5 : 1,
              }}
            >
              {btnLabel}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main client component ──────────────────────────────────────────────────────

interface AutomationControlsClientProps {
  initialLoop: AutonomousLoopPayload;
  initialTasks: BackendTask[];
  initialSummary: Record<string, number>;
}

export default function AutomationControlsClient({
  initialLoop,
  initialTasks,
  initialSummary,
}: AutomationControlsClientProps) {
  const [loop, setLoop] = useState<AutonomousLoopPayload>(initialLoop);
  const [tasks, setTasks] = useState<BackendTask[]>(initialTasks);
  const [summary, setSummary] = useState(initialSummary);
  const [loopLoading, setLoopLoading] = useState(false);
  const [taskLoading, setTaskLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshLoop = useCallback(async () => {
    try {
      const data = await proxyPost<AutonomousLoopPayload>("/api/autonomous_loop", {
        action: "status",
      });
      setLoop(data);
    } catch {}
  }, []);

  const refreshTasks = useCallback(async () => {
    try {
      const data = await proxyPost<{ ok: boolean; tasks: BackendTask[]; summary: Record<string, unknown> }>(
        "/api/tasks",
        { action: "list", limit: 50 }
      );
      setTasks(data.tasks ?? []);
      const counts = (data.summary?.counts ?? {}) as Record<string, number>;
      setSummary(counts);
    } catch {}
  }, []);

  // Poll every 8s while mounted
  useEffect(() => {
    const id = setInterval(() => {
      refreshLoop();
      refreshTasks();
    }, 8000);
    return () => clearInterval(id);
  }, [refreshLoop, refreshTasks]);

  const handleLoopAction = async (action: string) => {
    setLoopLoading(true);
    setError(null);
    try {
      const data = await proxyPost<AutonomousLoopPayload>("/api/autonomous_loop", { action });
      if (data.requires_confirmation) {
        setError(data.msg ?? "Confirmation requise — ATHOS_AUTONOMOUS_LOOP_ENABLED absent");
      } else {
        setLoop(data);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoopLoading(false);
    }
  };

  const handleTaskAction = async (taskId: string, action: string) => {
    setTaskLoading(true);
    setError(null);
    try {
      await proxyPost("/api/tasks", { action, task_id: taskId });
      await refreshTasks();
    } catch (err) {
      setError(String(err));
    } finally {
      setTaskLoading(false);
    }
  };

  const activeCount =
    (summary.queued ?? 0) +
    (summary.running ?? 0) +
    (summary.paused ?? 0) +
    (summary.blocked ?? 0);

  return (
    <div>
      {/* ── Error notice ── */}
      {error && (
        <div
          style={{
            background: "rgba(255,69,58,0.08)",
            border: "1px solid rgba(255,69,58,0.25)",
            borderRadius: 6,
            padding: "8px 14px",
            fontSize: 12,
            color: "var(--red)",
            marginBottom: 16,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>⛔ {error}</span>
          <button
            onClick={() => setError(null)}
            style={{ background: "none", border: "none", color: "var(--red)", cursor: "pointer", fontSize: 14 }}
          >
            ×
          </button>
        </div>
      )}

      {/* ── Boucle autonome ── */}
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "16px 20px",
          marginBottom: 20,
        }}
      >
        <div
          style={{
            fontSize: 11,
            letterSpacing: 1.5,
            color: "var(--muted)",
            textTransform: "uppercase",
            fontWeight: 600,
            marginBottom: 14,
          }}
        >
          Boucle autonome — RÉEL
        </div>
        <LoopControls loop={loop} onAction={handleLoopAction} loading={loopLoading} />
      </div>

      {/* ── Task queue ── */}
      <div>
        <div
          style={{
            fontSize: 11,
            letterSpacing: 1.5,
            color: "var(--muted)",
            textTransform: "uppercase",
            fontWeight: 600,
            marginBottom: 10,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>
            Task Queue — RÉEL
            {activeCount > 0 && (
              <span
                style={{
                  marginLeft: 8,
                  background: "rgba(120,60,255,0.15)",
                  color: "var(--accent)",
                  borderRadius: 20,
                  padding: "1px 7px",
                  fontSize: 10,
                  fontWeight: 700,
                }}
              >
                {activeCount} actives
              </span>
            )}
          </span>
          {tasks.length > 0 && (
            <button
              onClick={refreshTasks}
              disabled={taskLoading}
              style={{
                fontSize: 10,
                padding: "2px 8px",
                borderRadius: 4,
                border: "1px solid var(--border)",
                background: "none",
                color: "var(--muted)",
                cursor: "pointer",
              }}
            >
              ⟳ Rafraîchir
            </button>
          )}
        </div>

        {tasks.length === 0 ? (
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
            <div style={{ fontSize: 11, color: "var(--border)" }}>
              Aucune tâche · Les tâches apparaissent quand ATHOS travaille
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
            {tasks.map((task, i) => (
              <div
                key={task.id}
                style={{
                  borderBottom: i < tasks.length - 1 ? "1px solid var(--border)" : "none",
                }}
              >
                <TaskRow task={task} onAction={handleTaskAction} loading={taskLoading} />
              </div>
            ))}
            {tasks.length >= 50 && (
              <div
                style={{
                  padding: "8px 16px",
                  fontSize: 11,
                  color: "var(--border)",
                  borderTop: "1px solid var(--border)",
                }}
              >
                Affichage limité à 50 tâches
              </div>
            )}
          </div>
        )}

        {/* Counts bar */}
        {Object.keys(summary).filter((k) => summary[k] > 0).length > 0 && (
          <div
            style={{
              display: "flex",
              gap: 12,
              marginTop: 10,
              flexWrap: "wrap",
            }}
          >
            {Object.entries(summary)
              .filter(([, v]) => v > 0)
              .map(([status, count]) => (
                <span
                  key={status}
                  style={{
                    fontSize: 10,
                    color: TASK_COLORS[status] ?? "var(--muted)",
                    fontFamily: "monospace",
                  }}
                >
                  {count} {TASK_LABELS[status] ?? status}
                </span>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
