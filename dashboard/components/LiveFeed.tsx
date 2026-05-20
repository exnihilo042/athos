"use client";
import { useEffect, useRef, useState } from "react";

interface FeedItem {
  type: string;
  ts: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Record<string, any>;
}

const TYPE_COLOR: Record<string, string> = {
  status: "var(--blue)",
  session_event: "var(--accent)",
  error: "var(--red)",
};

function label(item: FeedItem): string {
  const d = item.data;
  if (item.type === "status") return `moteur: ${d.engine ?? "—"} · ${d.degraded ? "dégradé" : "OK"}`;
  if (item.type === "session_event") {
    const t = d.t ?? d.type ?? d.name ?? item.type;
    return String(t).slice(0, 80);
  }
  if (item.type === "error") return `erreur: ${d.error ?? "inconnu"}`;
  return item.type;
}

export default function LiveFeed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [connected, setConnected] = useState<"connecting" | "ok" | "error">("connecting");
  const esRef = useRef<EventSource | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;
      setConnected("connecting");
      const es = new EventSource("/api/athos-events");
      esRef.current = es;

      es.onopen = () => { if (!cancelled) setConnected("ok"); };

      const handle = (type: string) => (e: Event) => {
        if (cancelled) return;
        try {
          const data = JSON.parse((e as MessageEvent).data);
          setItems((prev) => [{ type, ts: Date.now(), data }, ...prev.slice(0, 29)]);
        } catch {}
      };

      es.addEventListener("status", handle("status"));
      es.addEventListener("session_event", handle("session_event"));
      es.addEventListener("error", handle("error"));

      es.onerror = () => {
        if (cancelled) return;
        setConnected("error");
        es.close();
        retryRef.current = setTimeout(connect, 5000);
      };
    }

    connect();

    return () => {
      cancelled = true;
      esRef.current?.close();
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  }, []);

  const dot =
    connected === "ok" ? "var(--green)" :
    connected === "error" ? "var(--red)" :
    "var(--border)";

  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: dot, boxShadow: `0 0 4px ${dot}`, display: "inline-block", flexShrink: 0 }} />
        <span style={{ fontSize: 11, letterSpacing: 1.2, color: "var(--muted)", textTransform: "uppercase", fontWeight: 600 }}>
          Live Events
        </span>
        {connected === "error" && (
          <span style={{ fontSize: 10, color: "var(--red)", marginLeft: 4 }}>reconnexion…</span>
        )}
        {connected === "connecting" && (
          <span style={{ fontSize: 10, color: "var(--muted)", marginLeft: 4 }}>connexion…</span>
        )}
      </div>

      {items.length === 0 ? (
        <div style={{ padding: "24px 16px", textAlign: "center", color: "var(--border)", fontSize: 12 }}>
          En attente d'événements…
        </div>
      ) : (
        <div style={{ maxHeight: 320, overflowY: "auto" }}>
          {items.map((item, i) => {
            const color = TYPE_COLOR[item.type] ?? "var(--muted)";
            return (
              <div key={i} style={{
                display: "flex", gap: 10, padding: "8px 16px",
                borderBottom: i < items.length - 1 ? "1px solid var(--border)" : "none",
                alignItems: "flex-start",
              }}>
                <span style={{ color, fontSize: 9, marginTop: 4, flexShrink: 0 }}>●</span>
                <span style={{ fontSize: 12, color: "var(--text)", flex: 1, minWidth: 0, wordBreak: "break-word" }}>
                  {label(item)}
                </span>
                <span style={{ fontSize: 10, color: "var(--border)", whiteSpace: "nowrap", flexShrink: 0 }}>
                  {new Date(item.ts).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
