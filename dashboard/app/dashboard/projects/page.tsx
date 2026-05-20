import { athosPost } from "@/lib/athos";

interface Project {
  name: string;
  status?: string;
  priority?: string;
  stack?: string;
  local?: string;
  state?: string;
  next?: string;
  blocker?: string;
  memory?: string;
  store?: string;
  repo?: string;
  [key: string]: string | undefined;
}

interface ProjectsPayload {
  projects?: Project[];
}

const STATUS_COLOR: Record<string, string> = {
  active: "var(--green)",
  building: "var(--accent)",
  pending: "var(--border)",
  done: "var(--muted)",
};

const PRIORITY_LABEL: Record<string, string> = {
  "0": "P0",
  "1": "P1",
  "2": "P2",
  "3": "P3",
  "4": "P4",
  "5": "P5",
  "6": "P6",
};

function StatusBadge({ status }: { status?: string }) {
  const s = status ?? "unknown";
  const color = STATUS_COLOR[s] ?? "var(--muted)";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "2px 8px", borderRadius: 20, fontSize: 11,
      background: `${color}18`,
      color,
      border: `1px solid ${color}30`,
    }}>
      <span style={{ fontSize: 7 }}>●</span>{s}
    </span>
  );
}

function PriorityBadge({ priority }: { priority?: string }) {
  if (!priority) return null;
  const label = PRIORITY_LABEL[priority] ?? `P${priority}`;
  const p = parseInt(priority, 10);
  const color = p === 0 ? "var(--red)" : p <= 2 ? "var(--yellow)" : "var(--border)";
  return (
    <span style={{
      display: "inline-flex", padding: "1px 6px", borderRadius: 4, fontSize: 10,
      fontWeight: 700, letterSpacing: 0.5,
      background: `${color}18`, color, border: `1px solid ${color}30`,
    }}>
      {label}
    </span>
  );
}

function ProjectCard({ proj }: { proj: Project }) {
  const localCmd = proj.local?.replace(/_/g, " ");
  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8,
      padding: 16, display: "flex", flexDirection: "column", gap: 10,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text)" }}>{proj.name}</span>
        <StatusBadge status={proj.status} />
        <PriorityBadge priority={proj.priority} />
      </div>

      {proj.stack && (
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          <span style={{ color: "var(--border)", marginRight: 6 }}>Stack</span>
          <span style={{ color: "var(--text)" }}>{proj.stack.replace(/_/g, " ")}</span>
        </div>
      )}

      {proj.state && (
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          <span style={{ color: "var(--border)", marginRight: 6 }}>État</span>
          <span style={{ color: "var(--text)" }}>{proj.state.replace(/_/g, " ")}</span>
        </div>
      )}

      {proj.next && (
        <div style={{ fontSize: 12 }}>
          <span style={{ color: "var(--border)", marginRight: 6 }}>→</span>
          <span style={{ color: "var(--accent)" }}>{proj.next.replace(/_/g, " ")}</span>
        </div>
      )}

      {proj.blocker && (
        <div style={{ fontSize: 12 }}>
          <span style={{ color: "var(--red)", marginRight: 6 }}>⚠</span>
          <span style={{ color: "var(--red)" }}>{proj.blocker.replace(/_/g, " ").replace(/\[/g, "").replace(/\]/g, "")}</span>
        </div>
      )}

      {localCmd && (
        <div style={{
          marginTop: 4, fontFamily: "monospace", fontSize: 11, color: "var(--muted)",
          background: "var(--surface-2)", borderRadius: 4, padding: "4px 8px",
          wordBreak: "break-all",
        }}>
          {localCmd}
        </div>
      )}

      {(proj.store || proj.repo) && (
        <div style={{ fontSize: 11, color: "var(--border)" }}>
          {proj.store && <span>◳ {proj.store}{"  "}</span>}
          {proj.repo && <span>⎇ {proj.repo}</span>}
        </div>
      )}
    </div>
  );
}

export default async function ProjectsPage() {
  let data: ProjectsPayload = {};

  try {
    data = await athosPost<ProjectsPayload>("/api/projects");
  } catch {}

  const projects = (data.projects ?? []).sort((a, b) => {
    const pa = parseInt(a.priority ?? "99", 10);
    const pb = parseInt(b.priority ?? "99", 10);
    return pa - pb;
  });

  const active = projects.filter((p) => p.status === "active" || p.status === "building");
  const pending = projects.filter((p) => p.status === "pending" || !p.status);

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Sites & Projets</h1>
        <p style={{ color: "var(--muted)", fontSize: 13, margin: 0 }}>
          {projects.length} projets · source : athos_projects.mem
        </p>
      </div>

      {active.length > 0 && (
        <>
          <div style={{ fontSize: 11, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 12 }}>
            Actifs — {active.length}
          </div>
          <div className="grid-auto-2" style={{ marginBottom: 24 }}>
            {active.map((proj) => (
              <ProjectCard key={proj.name} proj={proj} />
            ))}
          </div>
        </>
      )}

      {pending.length > 0 && (
        <>
          <div style={{ fontSize: 11, letterSpacing: 1.5, color: "var(--border)", textTransform: "uppercase", marginBottom: 12 }}>
            En attente — {pending.length}
          </div>
          <div className="grid-auto-2">
            {pending.map((proj) => (
              <ProjectCard key={proj.name} proj={proj} />
            ))}
          </div>
        </>
      )}

      {projects.length === 0 && (
        <div style={{ padding: "40px 0", textAlign: "center", color: "var(--border)", fontSize: 13 }}>
          Aucun projet — athos_projects.mem inaccessible ou vide
        </div>
      )}
    </div>
  );
}
