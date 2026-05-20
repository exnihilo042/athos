"use client";
import { useEffect, useState } from "react";

interface StatusData {
  engine?: string;
  budget?: number;
  degraded?: boolean;
  capability_graph?: { summary?: { nodes?: number; available_nodes?: number } };
  session?: { events?: number };
}

const DOT = {
  ok: { color: "var(--green)", label: "opérationnel" },
  warn: { color: "var(--yellow)", label: "dégradé" },
  err: { color: "var(--red)", label: "erreur" },
};

export default function TopBar() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/athos-proxy", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ endpoint: "/api/status" }),
        });
        if (res.ok) setStatus(await res.json());
      } catch {}
    };
    load();
    const id = setInterval(() => { load(); setTick((t) => t + 1); }, 30000);
    return () => clearInterval(id);
  }, []);

  const dot = status ? (status.degraded ? DOT.warn : DOT.ok) : DOT.err;

  return (
    <header
      style={{
        height: 44,
        background: "var(--surface)",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        padding: "0 20px",
        gap: 20,
        fontSize: 12,
        color: "var(--muted)",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          color: "var(--text)",
          fontWeight: 600,
          letterSpacing: 1,
        }}
      >
        <span
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: dot.color,
            boxShadow: `0 0 6px ${dot.color}`,
          }}
        />
        ATHOS
      </span>

      <span style={{ color: "var(--border)" }}>|</span>

      <span>
        Moteur:{" "}
        <span style={{ color: "var(--accent)", fontWeight: 600 }}>
          {status?.engine ?? "—"}
        </span>
      </span>

      <span>
        Budget:{" "}
        <span style={{ color: "var(--text)" }}>
          {status?.budget !== undefined ? `${status.budget.toFixed(3)}€` : "—"}
        </span>
      </span>

      <span>
        Graph:{" "}
        <span style={{ color: "var(--text)" }}>
          {status?.capability_graph?.summary
            ? `${status.capability_graph.summary.available_nodes ?? 0}/${status.capability_graph.summary.nodes ?? 0} nœuds`
            : "—"}
        </span>
      </span>

      <span>
        Session:{" "}
        <span style={{ color: "var(--text)" }}>
          {status?.session?.events !== undefined ? `${status.session.events} events` : "—"}
        </span>
      </span>

      <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--border)" }}>
        {tick > 0 ? `↻ ${new Date().toLocaleTimeString("fr-FR")}` : "chargement…"}
      </span>
    </header>
  );
}
