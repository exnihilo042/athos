import { athosPost } from "@/lib/athos";

interface RoomEntry {
  id?: string;
  ts?: string;
  actor?: string;
  type?: string;
  content?: string;
  status?: string;
  task_id?: string;
}

interface ConversationPayload {
  thread?: RoomEntry[];
  summary?: { total?: number; actors?: Record<string, number> };
}

const ACTOR_COLOR: Record<string, string> = {
  clement: "var(--blue)",
  claude: "var(--accent)",
  codex: "var(--green)",
  athos: "var(--accent-2)",
};

const TYPE_BADGE: Record<string, { bg: string; color: string; label: string }> = {
  message: { bg: "rgba(74,158,255,0.15)", color: "var(--blue)", label: "msg" },
  result: { bg: "rgba(52,199,89,0.15)", color: "var(--green)", label: "result" },
  action: { bg: "rgba(170,90,255,0.15)", color: "var(--accent-2)", label: "action" },
  error: { bg: "rgba(255,69,58,0.15)", color: "var(--red)", label: "error" },
};

export default async function RoomPage() {
  let data: ConversationPayload = {};

  try {
    data = await athosPost<ConversationPayload>("/api/conversation", { action: "get", limit: 60 });
  } catch {}

  const thread = data.thread ?? [];
  const summary = data.summary ?? {};

  return (
    <div style={{ maxWidth: 860 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Room</h1>
          <p style={{ color: "var(--muted)", fontSize: 13 }}>
            {summary.total ?? 0} messages total
            {Object.keys(summary.actors ?? {}).length > 0 && (
              <> · {Object.entries(summary.actors ?? {}).map(([a, c]) => `${a}: ${c}`).join(", ")}</>
            )}
          </p>
        </div>
        <a
          href="http://localhost:7474"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: 12,
            color: "var(--accent)",
            border: "1px solid var(--border)",
            padding: "6px 14px",
            borderRadius: 6,
            textDecoration: "none",
          }}
        >
          Ouvrir Room complète →
        </a>
      </div>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          overflow: "hidden",
        }}
      >
        {thread.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--muted)" }}>Room vide</div>
        ) : (
          thread.map((entry) => {
            const actorColor = ACTOR_COLOR[entry.actor ?? ""] ?? "var(--muted)";
            const badge = TYPE_BADGE[entry.type ?? ""] ?? TYPE_BADGE.message;
            const ts = entry.ts ? new Date(entry.ts).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit" }) : "";

            return (
              <div
                key={entry.id}
                style={{
                  padding: "12px 20px",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  gap: 14,
                }}
              >
                <div style={{ minWidth: 64 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: actorColor }}>{entry.actor}</div>
                  <div style={{ fontSize: 10, color: "var(--border)" }}>{ts}</div>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 13,
                      color: entry.type === "error" ? "var(--red)" : "var(--text)",
                      lineHeight: 1.5,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                    }}
                  >
                    {entry.content}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                  <span
                    style={{
                      fontSize: 9,
                      padding: "2px 6px",
                      borderRadius: 3,
                      background: badge.bg,
                      color: badge.color,
                      letterSpacing: 0.5,
                    }}
                  >
                    {badge.label}
                  </span>
                  {entry.status && entry.status !== "completed" && (
                    <span style={{ fontSize: 9, color: "var(--muted)" }}>{entry.status}</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
