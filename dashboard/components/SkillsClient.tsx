"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Skill,
  SkillCategory,
  SkillMaturity,
  LifecyclePhase,
  UsageLevel,
  AthoAgent,
  CategoryMeta,
  AgentMeta,
  WorkflowTrigger,
  SKILL_CATEGORIES,
  getSkillById,
} from "@/lib/skill-registry";

// ── Constants ──────────────────────────────────────────────────────────────

const MATURITY_CONFIG: Record<SkillMaturity, { label: string; color: string; bg: string }> = {
  available_now:          { label: "DISPONIBLE",    color: "var(--green)",    bg: "rgba(52,199,89,0.10)" },
  strategic:              { label: "STRATÉGIQUE",   color: "var(--accent-2)", bg: "rgba(170,90,255,0.10)" },
  future_athos_integration: { label: "FUTUR ATHOS", color: "var(--blue)",    bg: "rgba(74,158,255,0.10)" },
};

const PHASE_LABELS: Record<LifecyclePhase, string> = {
  planning:       "Planning",
  design:         "Design",
  implementation: "Implem.",
  review:         "Review",
  qa:             "QA",
  ship:           "Ship",
  monitoring:     "Monitor",
  memory:         "Mémoire",
};

const USAGE_LABELS: Record<UsageLevel, string> = {
  operator:    "Opérateur",
  product:     "Produit",
  engineering: "Eng.",
  qa:          "QA",
  strategy:    "Stratégie",
  automation:  "Auto.",
};

// ── Highlight helper ───────────────────────────────────────────────────────

function highlight(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <mark style={{ background: "rgba(120,60,255,0.25)", color: "var(--text)", borderRadius: 2 }}>
        {text.slice(idx, idx + query.length)}
      </mark>
      {text.slice(idx + query.length)}
    </>
  );
}

// ── SkillCard ──────────────────────────────────────────────────────────────

function SkillCard({ skill, filterText }: { skill: Skill; filterText: string }) {
  const [expanded, setExpanded] = useState(false);
  const mat = MATURITY_CONFIG[skill.maturity];
  const primaryCat = skill.categories[0];
  const catMeta = SKILL_CATEGORIES[primaryCat];

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderTop: `2px solid ${catMeta.color}`,
        borderRadius: 8,
        padding: "14px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
        cursor: "pointer",
        transition: "border-color 0.15s",
      }}
      onClick={() => setExpanded((v) => !v)}
    >
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 3, flex: 1, minWidth: 0 }}>
          <span
            style={{
              fontFamily: "monospace",
              fontSize: 13,
              fontWeight: 700,
              color: "var(--accent)",
              letterSpacing: 0.3,
            }}
          >
            {highlight(skill.slash, filterText)}
          </span>
          <span style={{ fontSize: 11, color: "var(--muted)" }}>
            {highlight(skill.name, filterText)}
          </span>
        </div>
        {/* Maturity badge */}
        <span
          style={{
            fontSize: 8,
            fontWeight: 700,
            letterSpacing: 0.8,
            color: mat.color,
            background: mat.bg,
            border: `1px solid ${mat.color}`,
            borderRadius: 3,
            padding: "2px 5px",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          {mat.label}
        </span>
      </div>

      {/* Description */}
      <p style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5, margin: 0 }}>
        {highlight(skill.description, filterText)}
      </p>

      {/* Phase pills */}
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {skill.lifecycle_phases.map((p) => (
          <span
            key={p}
            style={{
              fontSize: 9,
              fontWeight: 600,
              letterSpacing: 0.5,
              color: "var(--border)",
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              borderRadius: 3,
              padding: "1px 5px",
            }}
          >
            {PHASE_LABELS[p]}
          </span>
        ))}
        {skill.categories.map((c) => (
          <span
            key={c}
            style={{
              fontSize: 9,
              fontWeight: 600,
              color: SKILL_CATEGORIES[c].color,
              background: "var(--surface-2)",
              borderRadius: 3,
              padding: "1px 5px",
              opacity: 0.8,
            }}
          >
            {SKILL_CATEGORIES[c].icon}
          </span>
        ))}
      </div>

      {/* ATHOS recommendation — always visible */}
      <div
        style={{
          fontSize: 11,
          color: "var(--accent-2)",
          fontStyle: "italic",
          borderLeft: "2px solid rgba(170,90,255,0.3)",
          paddingLeft: 8,
        }}
      >
        ATHOS recommande : {skill.athos_recommendation}
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: 10,
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Usage levels */}
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 9, color: "var(--border)", textTransform: "uppercase", letterSpacing: 1 }}>Usage</span>
            {skill.usage_levels.map((u) => (
              <span
                key={u}
                style={{
                  fontSize: 9,
                  color: "var(--muted)",
                  background: "var(--surface-2)",
                  borderRadius: 3,
                  padding: "1px 5px",
                  border: "1px solid var(--border)",
                }}
              >
                {USAGE_LABELS[u]}
              </span>
            ))}
          </div>

          {/* Recommended for */}
          <div>
            <div style={{ fontSize: 9, color: "var(--border)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Recommandé pour</div>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {skill.recommended_for.map((r) => (
                <span key={r} style={{ fontSize: 10, color: "var(--muted)" }}>· {r}</span>
              ))}
            </div>
          </div>

          {/* Agents */}
          <div>
            <div style={{ fontSize: 9, color: "var(--border)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Agents ATHOS</div>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {skill.agents.map((a) => (
                <span
                  key={a}
                  style={{
                    fontSize: 9,
                    fontWeight: 600,
                    color: "var(--blue)",
                    background: "rgba(74,158,255,0.08)",
                    border: "1px solid rgba(74,158,255,0.2)",
                    borderRadius: 3,
                    padding: "1px 5px",
                  }}
                >
                  {a.replace("_", " ")}
                </span>
              ))}
            </div>
          </div>

          {/* ATHOS integration flag */}
          {skill.athos_integration && (
            <div
              style={{
                fontSize: 10,
                color: "var(--accent)",
                display: "flex",
                alignItems: "center",
                gap: 5,
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", display: "inline-block" }} />
              Intégrable dans orchestration ATHOS future
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── RecommendationEngine ───────────────────────────────────────────────────

function RecommendationEngine({ workflows }: { workflows: WorkflowTrigger[] }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        overflow: "hidden",
        marginBottom: 24,
      }}
    >
      <div
        style={{
          padding: "10px 16px",
          borderBottom: "1px solid var(--border)",
          background: "var(--surface-2)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase" }}>
          ⬡ Skill Recommendation Engine
        </span>
        <span
          style={{
            fontSize: 9,
            fontWeight: 600,
            color: "var(--blue)",
            background: "rgba(74,158,255,0.08)",
            border: "1px solid rgba(74,158,255,0.2)",
            borderRadius: 3,
            padding: "2px 6px",
          }}
        >
          FUTUR ATHOS
        </span>
      </div>

      <div style={{ padding: "12px 16px 4px" }}>
        <p style={{ fontSize: 12, color: "var(--muted)", margin: "0 0 12px", lineHeight: 1.5 }}>
          Aujourd'hui : visualisation manuelle. Demain : ATHOS suggère automatiquement le bon skill dans la Room selon le contexte projet, la phase, et l'activité en cours.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 8, marginBottom: 12 }}>
          {workflows.map((wf) => {
            const skill = getSkillById(wf.skill_id);
            return (
              <div
                key={wf.skill_id + wf.trigger}
                style={{
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: "10px 12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 5,
                }}
              >
                <div style={{ fontSize: 11, color: "var(--muted)" }}>{wf.trigger}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, fontFamily: "monospace", color: "var(--accent)" }}>
                    {skill?.slash ?? `/${wf.skill_id}`}
                  </span>
                  <span style={{ fontSize: 10, color: "var(--border)" }}>→</span>
                  <span style={{ fontSize: 10, color: "var(--muted)", fontStyle: "italic" }}>{wf.when}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── AgentSkillMatrix ───────────────────────────────────────────────────────

function AgentSkillMatrix({
  agents,
  skills,
}: {
  agents: Record<AthoAgent, AgentMeta>;
  skills: Skill[];
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: 1.5,
          color: "var(--muted)",
          textTransform: "uppercase",
          marginBottom: 12,
        }}
      >
        ⬡ Agent × Skill Matrix
      </div>
      <div className="grid-auto-2" style={{ gap: 10 }}>
        {(Object.entries(agents) as [AthoAgent, AgentMeta][]).map(([agentId, meta]) => {
          const agentSkills = skills.filter((s) => s.agents.includes(agentId));
          const available = agentSkills.filter((s) => s.maturity === "available_now");
          const strategic = agentSkills.filter((s) => s.maturity === "strategic");
          return (
            <div
              key={agentId}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderLeft: `3px solid ${meta.color}`,
                borderRadius: 8,
                padding: "12px 14px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{meta.label}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{meta.description}</div>
                </div>
                <span
                  style={{
                    fontSize: 18,
                    color: meta.color,
                    opacity: 0.6,
                    flexShrink: 0,
                  }}
                >
                  {meta.primary_categories.map((c) => SKILL_CATEGORIES[c].icon).join("")}
                </span>
              </div>

              {/* Skills pills */}
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                {available.map((s) => (
                  <span
                    key={s.id}
                    style={{
                      fontSize: 9,
                      fontWeight: 600,
                      fontFamily: "monospace",
                      color: "var(--green)",
                      background: "rgba(52,199,89,0.08)",
                      border: "1px solid rgba(52,199,89,0.2)",
                      borderRadius: 3,
                      padding: "1px 5px",
                    }}
                  >
                    {s.slash}
                  </span>
                ))}
                {strategic.map((s) => (
                  <span
                    key={s.id}
                    style={{
                      fontSize: 9,
                      fontFamily: "monospace",
                      color: "var(--border)",
                      background: "var(--surface-2)",
                      border: "1px solid var(--border)",
                      borderRadius: 3,
                      padding: "1px 5px",
                    }}
                  >
                    {s.slash}
                  </span>
                ))}
              </div>

              <div style={{ marginTop: 8, fontSize: 10, color: "var(--border)" }}>
                {available.length} disponibles · {strategic.length} stratégiques
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main client ────────────────────────────────────────────────────────────

interface Props {
  skills: Skill[];
  stats: { total: number; categories: number; available_now: number; strategic: number; future_athos: number; athos_integration: number };
  workflows: WorkflowTrigger[];
  agents: Record<AthoAgent, AgentMeta>;
}

export default function SkillsClient({ skills, stats, workflows, agents }: Props) {
  const [filterText, setFilterText]           = useState("");
  const [filterCategories, setFilterCategories] = useState<Set<SkillCategory>>(new Set());
  const [filterPhases, setFilterPhases]       = useState<Set<LifecyclePhase>>(new Set());
  const [filterMaturity, setFilterMaturity]   = useState<Set<SkillMaturity>>(new Set());
  const [filterAthos, setFilterAthos]         = useState(false);

  const toggleSet = <T,>(set: Set<T>, value: T): Set<T> => {
    const next = new Set(set);
    next.has(value) ? next.delete(value) : next.add(value);
    return next;
  };

  const filteredSkills = useMemo(() => {
    let r = skills;
    if (filterText.trim()) {
      const q = filterText.toLowerCase();
      r = r.filter((s) =>
        s.slash.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        s.recommended_for.some((x) => x.toLowerCase().includes(q))
      );
    }
    if (filterCategories.size > 0) {
      r = r.filter((s) => s.categories.some((c) => filterCategories.has(c)));
    }
    if (filterPhases.size > 0) {
      r = r.filter((s) => s.lifecycle_phases.some((p) => filterPhases.has(p)));
    }
    if (filterMaturity.size > 0) {
      r = r.filter((s) => filterMaturity.has(s.maturity));
    }
    if (filterAthos) {
      r = r.filter((s) => s.athos_integration);
    }
    return r;
  }, [skills, filterText, filterCategories, filterPhases, filterMaturity, filterAthos]);

  const hasFilters =
    filterText.trim() ||
    filterCategories.size > 0 ||
    filterPhases.size > 0 ||
    filterMaturity.size > 0 ||
    filterAthos;

  const resetFilters = () => {
    setFilterText("");
    setFilterCategories(new Set());
    setFilterPhases(new Set());
    setFilterMaturity(new Set());
    setFilterAthos(false);
  };

  // Phase list from all skills (sorted)
  const allPhases: LifecyclePhase[] = ["planning", "design", "implementation", "review", "qa", "ship", "monitoring", "memory"];

  return (
    <>
      {/* ── KPI Stats ── */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        {[
          { label: "Skills disponibles",    value: stats.available_now,      sub: `${stats.total} au total`,              color: "var(--green)" },
          { label: "Catégories",            value: stats.categories,          sub: "11 domaines opératoires",              color: "var(--text)" },
          { label: "Stratégiques",          value: stats.strategic,           sub: "à intégrer dans ATHOS",                color: "var(--accent-2)" },
          { label: "Intégrables ATHOS",     value: stats.athos_integration,   sub: "futur orchestration",                  color: "var(--accent)" },
        ].map(({ label, value, sub, color }) => (
          <div
            key={label}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "14px 16px",
            }}
          >
            <div style={{ fontSize: 28, fontWeight: 700, color, lineHeight: 1 }}>{value}</div>
            <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text)", marginTop: 4 }}>{label}</div>
            <div style={{ fontSize: 10, color: "var(--muted)", marginTop: 2 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* ── Filter bar ── */}
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "12px 14px",
          marginBottom: 20,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {/* Row 1 : search + results + reset */}
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input
            type="text"
            placeholder="Rechercher un skill, une commande, un usage…"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{
              flex: 1,
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: "7px 12px",
              fontSize: 12,
              color: "var(--text)",
              outline: "none",
            }}
          />
          <span style={{ fontSize: 11, color: "var(--muted)", whiteSpace: "nowrap" }}>
            {filteredSkills.length}/{stats.total}
          </span>
          {hasFilters && (
            <button
              onClick={resetFilters}
              style={{
                fontSize: 10,
                color: "var(--muted)",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 4,
                padding: "4px 8px",
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              ✕ Reset
            </button>
          )}
        </div>

        {/* Row 2 : category pills */}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 9, color: "var(--border)", textTransform: "uppercase", letterSpacing: 1, marginRight: 2 }}>Cat.</span>
          {(Object.entries(SKILL_CATEGORIES) as [SkillCategory, typeof SKILL_CATEGORIES[SkillCategory]][]).map(([cat, meta]) => {
            const active = filterCategories.has(cat);
            return (
              <button
                key={cat}
                onClick={() => setFilterCategories(toggleSet(filterCategories, cat))}
                style={{
                  fontSize: 10,
                  fontWeight: active ? 700 : 400,
                  color: active ? meta.color : "var(--muted)",
                  background: active ? `color-mix(in srgb, ${meta.color} 12%, transparent)` : "var(--surface-2)",
                  border: `1px solid ${active ? meta.color : "var(--border)"}`,
                  borderRadius: 4,
                  padding: "3px 8px",
                  cursor: "pointer",
                  transition: "all 0.12s",
                }}
              >
                {meta.icon} {meta.label}
              </button>
            );
          })}
        </div>

        {/* Row 3 : maturity + phase + athos toggle */}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 9, color: "var(--border)", textTransform: "uppercase", letterSpacing: 1, marginRight: 2 }}>Maturité</span>
          {(Object.entries(MATURITY_CONFIG) as [SkillMaturity, typeof MATURITY_CONFIG[SkillMaturity]][]).map(([mat, cfg]) => {
            const active = filterMaturity.has(mat);
            return (
              <button
                key={mat}
                onClick={() => setFilterMaturity(toggleSet(filterMaturity, mat))}
                style={{
                  fontSize: 9,
                  fontWeight: active ? 700 : 400,
                  color: active ? cfg.color : "var(--border)",
                  background: active ? cfg.bg : "var(--surface-2)",
                  border: `1px solid ${active ? cfg.color : "var(--border)"}`,
                  borderRadius: 4,
                  padding: "3px 7px",
                  cursor: "pointer",
                  transition: "all 0.12s",
                }}
              >
                {cfg.label}
              </button>
            );
          })}

          <span style={{ fontSize: 9, color: "var(--border)", textTransform: "uppercase", letterSpacing: 1, marginLeft: 6 }}>Phase</span>
          {allPhases.map((p) => {
            const active = filterPhases.has(p);
            return (
              <button
                key={p}
                onClick={() => setFilterPhases(toggleSet(filterPhases, p))}
                style={{
                  fontSize: 9,
                  color: active ? "var(--accent)" : "var(--border)",
                  background: active ? "rgba(120,60,255,0.10)" : "var(--surface-2)",
                  border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
                  borderRadius: 4,
                  padding: "3px 7px",
                  cursor: "pointer",
                  transition: "all 0.12s",
                }}
              >
                {PHASE_LABELS[p]}
              </button>
            );
          })}

          <button
            onClick={() => setFilterAthos((v) => !v)}
            style={{
              fontSize: 9,
              fontWeight: filterAthos ? 700 : 400,
              color: filterAthos ? "var(--accent)" : "var(--border)",
              background: filterAthos ? "rgba(120,60,255,0.12)" : "var(--surface-2)",
              border: `1px solid ${filterAthos ? "var(--accent)" : "var(--border)"}`,
              borderRadius: 4,
              padding: "3px 8px",
              cursor: "pointer",
              marginLeft: 6,
              transition: "all 0.12s",
            }}
          >
            ◈ Intégrables ATHOS
          </button>
        </div>
      </div>

      {/* ── Skills grid ── */}
      {filteredSkills.length === 0 ? (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "40px 24px",
            textAlign: "center",
            marginBottom: 24,
          }}
        >
          <div style={{ fontSize: 24, color: "var(--border)", marginBottom: 8 }}>◲</div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 4 }}>Aucun skill trouvé</div>
          <div style={{ fontSize: 11, color: "var(--border)" }}>Ajustez les filtres ou la recherche</div>
        </div>
      ) : (
        <div
          className="grid-auto-3"
          style={{ marginBottom: 28, gap: 12 }}
        >
          {filteredSkills.map((s) => (
            <SkillCard key={s.id} skill={s} filterText={filterText} />
          ))}
        </div>
      )}

      {/* ── Recommendation Engine ── */}
      <RecommendationEngine workflows={workflows} />

      {/* ── Agent × Skill Matrix ── */}
      <AgentSkillMatrix agents={agents} skills={skills} />

      {/* ── Backend notice ── */}
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "12px 16px",
          display: "flex",
          gap: 12,
          alignItems: "flex-start",
        }}
      >
        <span style={{ fontSize: 14, color: "var(--border)", flexShrink: 0 }}>◱</span>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)" }}>Catalogue local — données statiques</div>
          <div style={{ fontSize: 11, color: "var(--border)", marginTop: 3, lineHeight: 1.5 }}>
            Ce catalogue est défini dans <span style={{ fontFamily: "monospace" }}>dashboard/lib/skill-registry.ts</span>. Il ne reflète pas l'état runtime des skills installés — voir{" "}
            <Link href="/dashboard/automations" style={{ color: "var(--accent)", textDecoration: "none" }}>Automations</Link>{" "}
            pour l'état live via <span style={{ fontFamily: "monospace" }}>/api/skills</span>.
            Backend futur :{" "}
            <span style={{ fontFamily: "monospace", color: "var(--border)" }}>POST /api/skills/registry</span> ·{" "}
            <span style={{ fontFamily: "monospace", color: "var(--border)" }}>POST /api/skills/recommend</span> — Scope Codex P3.
          </div>
        </div>
      </div>
    </>
  );
}
