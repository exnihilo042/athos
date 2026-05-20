import { athosPost } from "@/lib/athos";
import { StatCard, SectionLabel, PageHeader, EmptyPanel } from "@/components/ui";

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

  const active  = projects.filter((p) => p.status === "active" || p.status === "building");
  const pending = projects.filter((p) => p.status === "pending" || !p.status);
  const done    = projects.filter((p) => p.status === "done");
  const blocked = projects.filter((p) => p.blocker);

  return (
    <div style={{ maxWidth: 1100 }}>
      <PageHeader
        title="Sites & Projets"
        subtitle={`Source : athos_projects.mem — ${projects.length} projet(s) chargé(s)`}
      />

      {/* ── KPIs ── */}
      {projects.length > 0 && (
        <div className="grid-auto-4" style={{ marginBottom: 24 }}>
          <StatCard label="Actifs"   value={active.length}  sub="en cours / en build" color={active.length > 0 ? "var(--green)" : "var(--muted)"} />
          <StatCard label="Bloqués"  value={blocked.length} sub="avec blocker déclaré" color={blocked.length > 0 ? "var(--red)" : "var(--muted)"} />
          <StatCard label="En attente" value={pending.length} sub="prêts à démarrer" color="var(--border)" />
          <StatCard label="Terminés" value={done.length}    sub="archivés" color="var(--muted)" />
        </div>
      )}

      {active.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <SectionLabel count={active.length}>Actifs</SectionLabel>
          <div className="grid-auto-2">
            {active.map((proj) => (
              <ProjectCard key={proj.name} proj={proj} />
            ))}
          </div>
        </div>
      )}

      {pending.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <SectionLabel count={pending.length}>En attente</SectionLabel>
          <div className="grid-auto-2">
            {pending.map((proj) => (
              <ProjectCard key={proj.name} proj={proj} />
            ))}
          </div>
        </div>
      )}

      {done.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <SectionLabel count={done.length}>Terminés</SectionLabel>
          <div className="grid-auto-2" style={{ opacity: 0.6 }}>
            {done.map((proj) => (
              <ProjectCard key={proj.name} proj={proj} />
            ))}
          </div>
        </div>
      )}

      {projects.length === 0 && (
        <EmptyPanel
          icon="◱"
          label="Aucun projet chargé"
          detail="athos_projects.mem inaccessible, vide ou endpoint /api/projects indisponible"
        />
      )}
    </div>
  );
}
