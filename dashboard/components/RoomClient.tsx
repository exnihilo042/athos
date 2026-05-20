"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { EngineBadge } from "@/components/ui";

interface RoomEntry {
  id?: string;
  ts?: string;
  actor?: string;
  type?: string;
  content?: string;
  status?: string;
  task_id?: string;
  meta?: Record<string, unknown>;
}

// ── Visual config ─────────────────────────────────────────────────────────────

const ACTOR_COLOR: Record<string, string> = {
  clement: "var(--blue)",
  claude: "var(--accent)",
  claude_code: "var(--accent)",
  codex: "var(--green)",
  chatgpt_plus: "var(--green)",
  athos: "var(--accent-2)",
};

const ACTOR_LABEL: Record<string, string> = {
  claude_code: "claude",
  chatgpt_plus: "codex",
};

interface TypeStyle {
  bg: string;
  color: string;
  label: string;
  icon: string;
}

const TYPE_STYLE: Record<string, TypeStyle> = {
  message: { bg: "rgba(74,158,255,0.12)", color: "var(--blue)", label: "msg", icon: "◉" },
  result: { bg: "rgba(52,199,89,0.12)", color: "var(--green)", label: "result", icon: "✓" },
  action: { bg: "rgba(170,90,255,0.12)", color: "var(--accent-2)", label: "action", icon: "⟳" },
  error: { bg: "rgba(255,69,58,0.12)", color: "var(--red)", label: "error", icon: "⚠" },
  report: { bg: "rgba(255,214,10,0.12)", color: "var(--yellow)", label: "report", icon: "◫" },
  checkpoint: { bg: "rgba(120,60,255,0.12)", color: "var(--accent)", label: "checkpoint", icon: "◈" },
  work: { bg: "rgba(74,158,255,0.08)", color: "var(--blue)", label: "work", icon: "◱" },
  summary: { bg: "rgba(170,90,255,0.08)", color: "var(--muted)", label: "summary", icon: "◪" },
};

const FALLBACK_TYPE: TypeStyle = { bg: "rgba(42,41,49,0.5)", color: "var(--muted)", label: "msg", icon: "◻" };

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTs(ts?: string): string {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function EngineStatusBar({
  connected,
  activeEngine,
  orchestrating,
}: {
  connected: "ok" | "error" | "connecting";
  activeEngine?: string;
  orchestrating?: boolean;
}) {
  const dotColor =
    connected === "ok" ? "var(--green)" :
    connected === "error" ? "var(--red)" :
    "var(--border)";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "6px 14px",
        background: "var(--surface-2)",
        borderRadius: 6,
        fontSize: 11,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: dotColor,
          boxShadow: connected === "ok" ? `0 0 4px ${dotColor}` : "none",
          flexShrink: 0,
          display: "inline-block",
        }}
      />
      <span style={{ color: "var(--muted)" }}>
        {connected === "connecting" ? "connexion SSE…" :
         connected === "error" ? "SSE hors ligne" :
         orchestrating ? "orchestration en cours" :
         "en écoute"}
      </span>
      {activeEngine && connected === "ok" && (
        <>
          <span style={{ color: "var(--border)" }}>·</span>
          <EngineBadge engine={activeEngine} />
        </>
      )}
    </div>
  );
}

const CONTENT_COLLAPSE_THRESHOLD = 500;

function RoomMessage({ entry }: { entry: RoomEntry }) {
  const [expanded, setExpanded] = useState(false);

  const actorColor = ACTOR_COLOR[entry.actor ?? ""] ?? "var(--muted)";
  const displayActor = ACTOR_LABEL[entry.actor ?? ""] ?? entry.actor ?? "?";
  const typeStyle = TYPE_STYLE[entry.type ?? ""] ?? FALLBACK_TYPE;
  const ts = formatTs(entry.ts);
  const isSystem = entry.actor === "athos";
  const isClement = entry.actor === "clement";
  const isError = entry.type === "error";
  const isCheckpoint = entry.type === "checkpoint";
  const isLong = (entry.content?.length ?? 0) > CONTENT_COLLAPSE_THRESHOLD;
  const displayContent = isLong && !expanded
    ? entry.content!.slice(0, CONTENT_COLLAPSE_THRESHOLD) + "…"
    : (entry.content ?? "");

  const contentColor = isError ? "var(--red)" :
    isCheckpoint ? "var(--accent)" :
    "var(--text)";

  // Checkpoint: full-width separator style
  if (isCheckpoint) {
    return (
      <div
        style={{
          padding: "12px 18px",
          borderBottom: "1px solid var(--border)",
          background: "rgba(120,60,255,0.06)",
          borderLeft: "3px solid var(--accent)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "var(--accent)", letterSpacing: 1, textTransform: "uppercase" }}>
            ◈ Checkpoint
          </span>
          <span style={{ fontSize: 9, color: "var(--border)" }}>{ts}</span>
          <span style={{ fontSize: 9, color: "var(--muted)", marginLeft: "auto" }}>{displayActor}</span>
        </div>
        <div style={{ fontSize: 12, color: "var(--accent)", lineHeight: 1.5, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {displayContent}
        </div>
        {isLong && (
          <button onClick={() => setExpanded(!expanded)} style={{ marginTop: 6, fontSize: 10, color: "var(--accent)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            {expanded ? "▲ réduire" : "▼ voir tout"}
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "9px 18px 9px 0",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        gap: 0,
        background: isClement ? "rgba(74,158,255,0.03)" : isError ? "rgba(255,69,58,0.03)" : "transparent",
        borderLeft: `3px solid ${isClement ? "var(--blue)" : isError ? "var(--red)" : actorColor}`,
      }}
    >
      {/* Actor column */}
      <div style={{ minWidth: 72, flexShrink: 0, paddingLeft: 12, paddingRight: 4 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: actorColor, letterSpacing: 0.3 }}>
          {displayActor}
        </div>
        <div style={{ fontSize: 9, color: "var(--border)", marginTop: 2 }}>{ts}</div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0, paddingRight: 12 }}>
        <div
          style={{
            fontSize: 12,
            color: contentColor,
            lineHeight: 1.55,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            opacity: isSystem && entry.type === "action" ? 0.7 : 1,
          }}
        >
          {displayContent}
        </div>
        {isLong && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              marginTop: 4,
              fontSize: 10,
              color: "var(--muted)",
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: 0,
              letterSpacing: 0.3,
            }}
          >
            {expanded ? "▲ réduire" : `▼ voir tout (${entry.content!.length} car.)`}
          </button>
        )}
        {entry.task_id && (
          <div style={{ marginTop: 4, fontSize: 9, color: "var(--border)", fontFamily: "monospace" }}>
            task:{truncate(entry.task_id, 12)}
          </div>
        )}
      </div>

      {/* Type badge */}
      <div style={{ flexShrink: 0, paddingTop: 1, paddingRight: 12 }}>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 3,
            fontSize: 9,
            padding: "2px 6px",
            borderRadius: 4,
            background: typeStyle.bg,
            color: typeStyle.color,
            fontWeight: 600,
            letterSpacing: 0.3,
          }}
        >
          {typeStyle.icon} {typeStyle.label}
        </span>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function RoomClient({
  initialThread,
  totalMessages,
}: {
  initialThread: RoomEntry[];
  totalMessages: number;
}) {
  const [thread, setThread] = useState<RoomEntry[]>(initialThread);
  const [input, setValue] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState("");
  const [total, setTotal] = useState(totalMessages);
  const [sseState, setSseState] = useState<"connecting" | "ok" | "error">("connecting");
  const [activeEngine, setActiveEngine] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/athos-proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: "/api/conversation",
          payload: { action: "get", limit: 60 },
        }),
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.thread) setThread(data.thread);
      if (data.summary?.total) setTotal(data.summary.total);
    } catch {}
  }, []);

  // SSE: real-time refresh trigger + engine status
  useEffect(() => {
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (cancelled) return;
      const es = new EventSource("/api/athos-events");
      esRef.current = es;

      es.onopen = () => { if (!cancelled) setSseState("ok"); };

      es.addEventListener("status", (e) => {
        try {
          const d = JSON.parse((e as MessageEvent).data);
          if (d.engine) setActiveEngine(d.engine);
        } catch {}
      });

      es.addEventListener("session_event", () => {
        if (!cancelled) refresh();
      });

      es.onerror = () => {
        if (cancelled) return;
        setSseState("error");
        es.close();
        retryTimer = setTimeout(connect, 8000);
      };
    }

    connect();
    return () => {
      cancelled = true;
      esRef.current?.close();
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [refresh]);

  // Fallback poll (8s) in case SSE misses events
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
      else if (response.scheduled) setStatus("Engine en cours de réponse…");
      else setStatus("Message ajouté.");
      await refresh();
      setTimeout(() => { refresh(); setStatus(""); }, 3000);
    } catch (e) {
      setStatus(`Erreur: ${String(e)}`);
    } finally {
      setSending(false);
    }
  }

  const orchestrating = !!status && status.includes("cours");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 12,
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 600, margin: 0 }}>Room</h1>
          <p style={{ color: "var(--muted)", fontSize: 13, margin: "3px 0 0" }}>
            {total} messages · mise à jour live
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <EngineStatusBar
            connected={sseState}
            activeEngine={activeEngine}
            orchestrating={orchestrating}
          />
          {status && (
            <span style={{ fontSize: 12, color: "var(--muted)" }}>{status}</span>
          )}
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
            ↻
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
            Room complète →
          </a>
        </div>
      </div>

      {/* Engine legend */}
      <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
        {[
          { actor: "clement", label: "Clément" },
          { actor: "claude", label: "Claude" },
          { actor: "codex", label: "Codex" },
          { actor: "athos", label: "ATHOS" },
        ].map(({ actor, label }) => (
          <span
            key={actor}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              fontSize: 10,
              color: ACTOR_COLOR[actor] ?? "var(--muted)",
              padding: "2px 8px",
              borderRadius: 20,
              background: "var(--surface-2)",
            }}
          >
            <span style={{ fontSize: 7 }}>●</span>
            {label}
          </span>
        ))}
        <span style={{ fontSize: 10, color: "var(--border)", alignSelf: "center" }}>·</span>
        {["message", "action", "result", "report", "error"].map((t) => {
          const s = TYPE_STYLE[t] ?? FALLBACK_TYPE;
          return (
            <span
              key={t}
              style={{
                fontSize: 9,
                padding: "2px 6px",
                borderRadius: 4,
                background: s.bg,
                color: s.color,
              }}
            >
              {s.icon} {t}
            </span>
          );
        })}
      </div>

      {/* Thread */}
      <div
        style={{
          flex: 1,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          overflowY: "auto",
          marginBottom: 12,
          minHeight: 360,
          maxHeight: "calc(100vh - 340px)",
        }}
      >
        {thread.length === 0 ? (
          <div style={{ padding: 60, textAlign: "center" }}>
            <div style={{ fontSize: 28, color: "var(--border)", marginBottom: 12 }}>◉</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--muted)", marginBottom: 6 }}>
              Room vide
            </div>
            <div style={{ fontSize: 12, color: "var(--border)", maxWidth: 280, margin: "0 auto", lineHeight: 1.5 }}>
              {sseState === "error"
                ? "Connexion SSE hors ligne — ATHOS HUB inaccessible. Vérifier :7474."
                : "Envoyer un message pour démarrer une session ATHOS."}
            </div>
          </div>
        ) : (
          thread.map((entry) => (
            <RoomMessage key={entry.id ?? entry.ts} entry={entry} />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
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
