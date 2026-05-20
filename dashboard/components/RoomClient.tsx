"use client";
import { useEffect, useRef, useState, useCallback } from "react";

interface RoomEntry {
  id?: string;
  ts?: string;
  actor?: string;
  type?: string;
  content?: string;
  status?: string;
  task_id?: string;
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

export default function RoomClient({ initialThread, totalMessages }: {
  initialThread: RoomEntry[];
  totalMessages: number;
}) {
  const [thread, setThread] = useState<RoomEntry[]>(initialThread);
  const [input, setValue] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState("");
  const [total, setTotal] = useState(totalMessages);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/athos-proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint: "/api/conversation", payload: { action: "get", limit: 60 } }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.thread) setThread(data.thread);
      if (data.summary?.total) setTotal(data.summary.total);
    } catch {}
  }, []);

  useEffect(() => {
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread.length]);

  async function send() {
    const content = input.trim();
    if (!content || sending) return;
    setSending(true);
    setValue("");
    setStatus("Envoi…");
    try {
      const res = await fetch("/api/athos-proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: "/api/message",
          payload: {
            actor: "clement",
            content,
            type: "message",
            task_id: `room-${Date.now()}`,
          },
        }),
      });
      const data = await res.json();
      const work = data.auto_work ?? {};
      const response = data.auto_response ?? {};
      if (work.scheduled) setStatus("Orchestration ATHOS en cours…");
      else if (response.scheduled) setStatus("Claude répond…");
      else setStatus("Message ajouté.");
      await refresh();
      setTimeout(() => { refresh(); setStatus(""); }, 3000);
    } catch (e) {
      setStatus(`Erreur: ${String(e)}`);
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, margin: 0 }}>Room</h1>
          <p style={{ color: "var(--muted)", fontSize: 13, margin: "4px 0 0" }}>
            {total} messages · rafraîchi toutes les 8s
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {status && <span style={{ fontSize: 12, color: "var(--muted)" }}>{status}</span>}
          <button
            onClick={refresh}
            style={{
              fontSize: 12,
              color: "var(--muted)",
              border: "1px solid var(--border)",
              background: "none",
              padding: "5px 12px",
              borderRadius: 5,
              cursor: "pointer",
            }}
          >
            ↻ Refresh
          </button>
          <a
            href="http://localhost:7474"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 12,
              color: "var(--accent)",
              border: "1px solid var(--border)",
              padding: "5px 12px",
              borderRadius: 5,
              textDecoration: "none",
            }}
          >
            Ouvrir Room complète →
          </a>
        </div>
      </div>

      <div
        style={{
          flex: 1,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          overflowY: "auto",
          marginBottom: 12,
          minHeight: 400,
          maxHeight: "calc(100vh - 300px)",
        }}
      >
        {thread.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--muted)" }}>Room vide</div>
        ) : (
          thread.map((entry) => {
            const actorColor = ACTOR_COLOR[entry.actor ?? ""] ?? "var(--muted)";
            const badge = TYPE_BADGE[entry.type ?? ""] ?? TYPE_BADGE.message;
            const ts = entry.ts
              ? new Date(entry.ts).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })
              : "";

            return (
              <div
                key={entry.id ?? entry.ts}
                style={{
                  padding: "10px 18px",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  gap: 12,
                }}
              >
                <div style={{ minWidth: 60 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: actorColor }}>{entry.actor}</div>
                  <div style={{ fontSize: 10, color: "var(--border)" }}>{ts}</div>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 12,
                      color: entry.type === "error" ? "var(--red)" : "var(--text)",
                      lineHeight: 1.5,
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                    }}
                  >
                    {entry.content}
                  </div>
                </div>
                <div style={{ flexShrink: 0 }}>
                  <span
                    style={{
                      fontSize: 9,
                      padding: "2px 5px",
                      borderRadius: 3,
                      background: badge.bg,
                      color: badge.color,
                    }}
                  >
                    {badge.label}
                  </span>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "8px 12px",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Message dans le fil ATHOS Room…"
          disabled={sending}
          style={{
            flex: 1,
            background: "none",
            border: "none",
            outline: "none",
            color: "var(--text)",
            fontSize: 13,
            padding: "4px 0",
          }}
        />
        <button
          onClick={send}
          disabled={sending || !input.trim()}
          style={{
            padding: "6px 16px",
            background: input.trim() && !sending ? "var(--accent)" : "var(--surface-2)",
            color: input.trim() && !sending ? "#fff" : "var(--muted)",
            border: "none",
            borderRadius: 6,
            fontSize: 12,
            cursor: input.trim() && !sending ? "pointer" : "default",
            transition: "all 0.15s",
          }}
        >
          {sending ? "…" : "Envoyer"}
        </button>
      </div>
    </div>
  );
}
