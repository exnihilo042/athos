import { athosPost } from "@/lib/athos";

interface GraphSummary {
  nodes?: number;
  edges?: number;
  available_nodes?: number;
  offline_ready_nodes?: number;
  available_engines?: string[];
  interconnection_score?: number;
  austere_mode_ready?: boolean;
}

interface CapabilityNode {
  id?: string;
  name?: string;
  type?: string;
  available?: boolean;
  offline_ready?: boolean;
  engines?: string[];
  description?: string;
}

interface CapabilityPayload {
  text?: string;
  graph?: {
    summary?: GraphSummary;
    nodes?: CapabilityNode[];
  };
  session?: { events?: number };
}

function NodeCard({ node }: { node: CapabilityNode }) {
  const available = node.available ?? false;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: `1px solid ${available ? "var(--border)" : "rgba(42,41,49,0.5)"}`,
        borderRadius: 6,
        padding: "10px 14px",
        opacity: available ? 1 : 0.45,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: available ? "var(--text)" : "var(--muted)" }}>
          {node.name ?? node.id}
        </span>
        <div style={{ display: "flex", gap: 4 }}>
          {available && (
            <span style={{ fontSize: 9, color: "var(--green)", background: "rgba(52,199,89,0.12)", padding: "1px 5px", borderRadius: 3 }}>
              ON
            </span>
          )}
          {node.offline_ready && (
            <span style={{ fontSize: 9, color: "var(--muted)", background: "var(--surface-2)", padding: "1px 5px", borderRadius: 3 }}>
              OFFLINE
            </span>
          )}
        </div>
      </div>
      {node.type && (
        <div style={{ fontSize: 10, color: "var(--accent)", letterSpacing: 0.5, textTransform: "uppercase" }}>
          {node.type}
        </div>
      )}
      {node.description && (
        <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4, lineHeight: 1.4 }}>
          {node.description}
        </div>
      )}
      {(node.engines ?? []).length > 0 && (
        <div style={{ fontSize: 10, color: "var(--border)", marginTop: 4 }}>
          {(node.engines ?? []).join(", ")}
        </div>
      )}
    </div>
  );
}

export default async function AgentsPage() {
  let data: CapabilityPayload = {};

  try {
    data = await athosPost<CapabilityPayload>("/api/capabilities");
  } catch {}

  const summary = data.graph?.summary;
  const nodes = data.graph?.nodes ?? [];
  const available = nodes.filter((n) => n.available);
  const unavailable = nodes.filter((n) => !n.available);

  return (
    <div style={{ maxWidth: 1100 }}>
      <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 6 }}>Agents IA</h1>
      <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 24 }}>
        Graphe de capacités — {summary?.nodes ?? 0} nœuds · {summary?.edges ?? 0} edges
      </p>

      {summary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
            gap: 12,
            marginBottom: 28,
          }}
        >
          {[
            { label: "Disponibles", value: summary.available_nodes, color: "var(--green)" },
            { label: "Total nœuds", value: summary.nodes, color: "var(--text)" },
            { label: "Edges", value: summary.edges, color: "var(--text)" },
            { label: "Offline-ready", value: summary.offline_ready_nodes, color: "var(--blue)" },
            { label: "Score", value: summary.interconnection_score?.toFixed(2), color: "var(--accent)" },
          ].map(({ label, value, color }) => (
            <div
              key={label}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                padding: "14px 16px",
              }}
            >
              <div style={{ fontSize: 22, fontWeight: 700, color }}>{value ?? "—"}</div>
              <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {summary?.available_engines && summary.available_engines.length === 0 && (
        <div
          style={{
            background: "rgba(255,69,58,0.08)",
            border: "1px solid rgba(255,69,58,0.25)",
            borderRadius: 6,
            padding: "12px 16px",
            fontSize: 13,
            color: "var(--red)",
            marginBottom: 24,
          }}
        >
          ⚠ Aucun engine disponible dans le graphe — capacity_graph.available_engines vide
        </div>
      )}

      {nodes.length > 0 ? (
        <>
          {available.length > 0 && (
            <>
              <h2 style={{ fontSize: 14, color: "var(--muted)", marginBottom: 12, letterSpacing: 1, textTransform: "uppercase" }}>
                Disponibles ({available.length})
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 10, marginBottom: 24 }}>
                {available.map((node) => <NodeCard key={node.id} node={node} />)}
              </div>
            </>
          )}
          {unavailable.length > 0 && (
            <>
              <h2 style={{ fontSize: 14, color: "var(--border)", marginBottom: 12, letterSpacing: 1, textTransform: "uppercase" }}>
                Non disponibles ({unavailable.length})
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 10 }}>
                {unavailable.map((node) => <NodeCard key={node.id} node={node} />)}
              </div>
            </>
          )}
        </>
      ) : (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: 40,
            textAlign: "center",
            color: "var(--muted)",
          }}
        >
          {data.text ? (
            <pre style={{ textAlign: "left", fontSize: 12, whiteSpace: "pre-wrap" }}>{data.text}</pre>
          ) : (
            "Graphe non disponible"
          )}
        </div>
      )}
    </div>
  );
}
