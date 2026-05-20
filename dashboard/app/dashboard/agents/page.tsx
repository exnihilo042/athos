import { athosPost } from "@/lib/athos";
import { StatCard, SectionLabel, PageHeader, EngineBadge, Badge } from "@/components/ui";
import Link from "next/link";

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
      <PageHeader
        title="Agents IA"
        subtitle={`Graphe de capacités ATHOS — ${nodes.length} nœuds · ${summary?.edges ?? "?"} edges`}
      >
        <Badge label="RÉEL" variant="green" />
      </PageHeader>

      {/* ── KPIs ── */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Nœuds disponibles"
          value={available}
          sub={`${unavailable} indisponibles`}
          color={available > 0 ? "var(--green)" : "var(--red)"}
          size="lg"
        />
        <StatCard
          label="Total nœuds"
          value={nodes.length}
          sub={`${summary?.edges ?? "?"} edges`}
          color="var(--text)"
        />
        <StatCard
          label="Offline-ready"
          value={summary?.offline_ready_nodes ?? "—"}
          sub="sans réseau"
          color="var(--blue)"
        />
        <StatCard
          label="Score graphe"
          value={summary?.interconnection_score?.toFixed(2) ?? "—"}
          sub={summary?.austere_mode_ready ? "austere mode OK" : "austere mode KO"}
          color={summary?.austere_mode_ready ? "var(--green)" : "var(--red)"}
        />
      </div>

      {/* ── Engines disponibles ── */}
      {(summary?.available_engines ?? []).length > 0 && (
        <div style={{ display: "flex", gap: 6, marginBottom: 24, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "var(--muted)", marginRight: 4 }}>Engines actifs</span>
          {(summary!.available_engines!).map((e) => (
            <EngineBadge key={e} engine={e} />
          ))}
        </div>
      )}

      {KIND_ORDER.filter((k) => byKind[k]?.length).map((kind) => {
        const kindNodes = byKind[kind];
        const kindAvail = kindNodes.filter((n) => STATUS_AVAILABLE.has(n.status)).length;
        return (
          <div key={kind} style={{ marginBottom: 24 }}>
            <SectionLabel count={kindNodes.length}>
              {KIND_ICON[kind] ?? "◻"} {kind.replace(/_/g, " ")}
              <span style={{ color: "var(--green)", fontSize: 10, marginLeft: 4 }}>{kindAvail} OK</span>
            </SectionLabel>
            <div className="grid-nodes">
              {kindNodes.map((node) => <NodeCard key={node.id} node={node} />)}
            </div>
          </div>
        );
      })}

      {Object.keys(byKind).filter((k) => !KIND_ORDER.includes(k)).map((kind) => (
        <div key={kind} style={{ marginBottom: 24 }}>
          <SectionLabel count={byKind[kind].length}>{kind.replace(/_/g, " ")}</SectionLabel>
          <div className="grid-nodes">
            {byKind[kind].map((node) => <NodeCard key={node.id} node={node} />)}
          </div>
        </div>
      ))}

      {/* ── Skills catalogue link ── */}
      <div style={{ marginTop: 8, marginBottom: 24 }}>
        <SectionLabel>Skills opérationnels</SectionLabel>
        <Link href="/dashboard/skills" style={{ textDecoration: "none" }}>
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderLeft: "3px solid var(--accent)",
              borderRadius: 8,
              padding: "14px 18px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 12,
              cursor: "pointer",
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 3 }}>
                ⬡ Skills & Capacités — Catalogue ATHOS
              </div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>
                47 skills documentés · 11 catégories · matrice agents × skills · moteur de recommandation
              </div>
            </div>
            <Badge label="VOIR →" variant="accent" />
          </div>
        </Link>
      </div>
    </div>
  );
}
