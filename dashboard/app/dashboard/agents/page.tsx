import { athosPost } from "@/lib/athos";

interface GraphNode {
  id: string;
  kind: string;
  label: string;
  status: string;
  offline: boolean;
  risk: string;
  cost: string;
  tags?: string[];
  meta?: Record<string, unknown>;
}

interface GraphPayload {
  nodes?: GraphNode[];
  principle?: string;
  summary?: {
    nodes?: number;
    edges?: number;
    available_nodes?: number;
    offline_ready_nodes?: number;
    available_engines?: string[];
    interconnection_score?: number;
    austere_mode_ready?: boolean;
  };
}

const STATUS_AVAILABLE = new Set(["active", "ok", "clear", "available", "configured", "integrated", "referenced"]);
const STATUS_BLOCKED = new Set(["missing", "blocked_by_zero_spend"]);

const STATUS_COLOR: Record<string, string> = {
  active: "var(--green)",
  ok: "var(--green)",
  clear: "var(--green)",
  available: "var(--green)",
  configured: "var(--blue)",
  integrated: "var(--blue)",
  referenced: "var(--muted)",
  planned: "var(--border)",
  missing: "var(--red)",
  blocked_by_zero_spend: "var(--yellow)",
};

const KIND_ICON: Record<string, string> = {
  identity: "◈",
  memory: "◫",
  engine: "⬡",
  local_tool: "◻",
  protocol: "◱",
  skill: "◲",
  device: "◾",
  hardware: "◼",
  guardrail: "⊙",
  sync: "⟳",
  capability: "◉",
  external_source: "◳",
  academic_source: "◳",
  model_profile: "⬡",
  review_stage: "◫",
  transport: "◱",
};

const KIND_ORDER = [
  "identity", "engine", "memory", "capability", "guardrail",
  "local_tool", "protocol", "skill", "sync", "device",
  "hardware", "model_profile", "review_stage", "external_source", "academic_source", "transport",
];

function NodeCard({ node }: { node: GraphNode }) {
  const isAvail = STATUS_AVAILABLE.has(node.status);
  const isBlocked = STATUS_BLOCKED.has(node.status);
  const isPlanned = node.status === "planned";
  const color = STATUS_COLOR[node.status] ?? "var(--muted)";

  return (
    <div
      style={{
        background: "var(--surface)",
        border: `1px solid ${isAvail ? "var(--border)" : "rgba(42,41,49,0.4)"}`,
        borderRadius: 6,
        padding: "10px 12px",
        opacity: isPlanned ? 0.4 : isBlocked ? 0.7 : 1,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: isAvail ? "var(--text)" : "var(--muted)", lineHeight: 1.3 }}>
          {KIND_ICON[node.kind] ?? "◻"} {node.label}
        </span>
        <span style={{ fontSize: 9, color, flexShrink: 0, padding: "1px 5px", background: "var(--surface-2)", borderRadius: 3 }}>
          {node.status}
        </span>
      </div>
      <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
        <span style={{ fontSize: 9, color: "var(--border)" }}>{node.kind}</span>
        {node.offline && (
          <span style={{ fontSize: 9, color: "var(--blue)" }}>offline</span>
        )}
        {node.cost !== "free" && (
          <span style={{ fontSize: 9, color: "var(--yellow)" }}>{node.cost}</span>
        )}
        {node.risk !== "low" && (
          <span style={{ fontSize: 9, color: "var(--red)" }}>risk:{node.risk}</span>
        )}
      </div>
    </div>
  );
}

export default async function AgentsPage() {
  let graphData: GraphPayload = {};
  let summaryData: { capability_graph?: GraphPayload["summary"] } = {};

  try {
    [graphData, summaryData] = await Promise.all([
      athosPost<GraphPayload>("/api/capability_graph"),
      athosPost<{ capability_graph?: GraphPayload["summary"] }>("/api/status"),
    ]);
  } catch {}

  const nodes = graphData.nodes ?? [];
  const summary = summaryData.capability_graph;

  const byKind: Record<string, GraphNode[]> = {};
  for (const node of nodes) {
    if (!byKind[node.kind]) byKind[node.kind] = [];
    byKind[node.kind].push(node);
  }

  const available = nodes.filter((n) => STATUS_AVAILABLE.has(n.status)).length;
  const unavailable = nodes.length - available;

  return (
    <div style={{ maxWidth: 1100 }}>
      <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 6 }}>Agents IA</h1>
      <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 24 }}>
        Graphe de capacités — {nodes.length} nœuds · {summary?.edges ?? "?"} edges
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 28 }}>
        {[
          { label: "Disponibles", value: available, color: "var(--green)" },
          { label: "Total nœuds", value: nodes.length, color: "var(--text)" },
          { label: "Offline-ready", value: summary?.offline_ready_nodes, color: "var(--blue)" },
          { label: "Engines actifs", value: (summary?.available_engines ?? []).length, color: "var(--accent)" },
          { label: "Austere OK", value: summary?.austere_mode_ready ? "✓" : "✗", color: summary?.austere_mode_ready ? "var(--green)" : "var(--red)" },
          { label: "Score graph", value: summary?.interconnection_score?.toFixed(2), color: "var(--muted)" },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 14px" }}>
            <div style={{ fontSize: 20, fontWeight: 700, color }}>{value ?? "—"}</div>
            <div style={{ fontSize: 10, color: "var(--muted)", marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>

      {(summary?.available_engines ?? []).length > 0 && (
        <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
          {(summary!.available_engines!).map((e) => (
            <span key={e} style={{ fontSize: 11, padding: "3px 10px", borderRadius: 20, background: "rgba(120,60,255,0.15)", color: "var(--accent)", border: "1px solid rgba(120,60,255,0.3)" }}>
              {e}
            </span>
          ))}
        </div>
      )}

      {KIND_ORDER.filter((k) => byKind[k]?.length).map((kind) => {
        const kindNodes = byKind[kind];
        const kindAvail = kindNodes.filter((n) => STATUS_AVAILABLE.has(n.status)).length;
        return (
          <div key={kind} style={{ marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
              <span style={{ fontSize: 11, letterSpacing: 1.2, color: "var(--muted)", textTransform: "uppercase", fontWeight: 600 }}>
                {KIND_ICON[kind] ?? "◻"} {kind.replace("_", " ")}
              </span>
              <span style={{ fontSize: 10, color: "var(--border)" }}>{kindAvail}/{kindNodes.length}</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
              {kindNodes.map((node) => <NodeCard key={node.id} node={node} />)}
            </div>
          </div>
        );
      })}

      {Object.keys(byKind).filter((k) => !KIND_ORDER.includes(k)).map((kind) => (
        <div key={kind} style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, letterSpacing: 1.2, color: "var(--muted)", textTransform: "uppercase", marginBottom: 10 }}>
            {kind}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
            {byKind[kind].map((node) => <NodeCard key={node.id} node={node} />)}
          </div>
        </div>
      ))}
    </div>
  );
}
