"use client";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { EngineBadge } from "@/components/ui";
import type { AthosStatus } from "@/lib/types";

// ── Types ──────────────────────────────────────────────────────────────────────

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

// ── Constants ──────────────────────────────────────────────────────────────────

const ACTOR_COLOR: Record<string, string> = {
  clement:     "var(--blue)",
  claude:      "var(--accent)",
  claude_code: "var(--accent)",
  codex:       "var(--green)",
  chatgpt_plus:"var(--green)",
  athos:       "var(--accent-2)",
};

const ACTOR_LABEL: Record<string, string> = {
  claude_code:  "claude",
  chatgpt_plus: "codex",
};

const ACTOR_DISPLAY: Record<string, string> = {
  clement:     "Clément",
  claude:      "Claude",
  claude_code: "Claude",
  codex:       "Codex",
  chatgpt_plus:"Codex",
  athos:       "ATHOS",
};

interface TypeStyle { bg: string; color: string; label: string; icon: string }

const TYPE_STYLE: Record<string, TypeStyle> = {
  message:    { bg: "rgba(74,158,255,0.12)",  color: "var(--blue)",     label: "msg",        icon: "◉" },
  result:     { bg: "rgba(52,199,89,0.12)",   color: "var(--green)",    label: "result",     icon: "✓" },
  action:     { bg: "rgba(170,90,255,0.12)",  color: "var(--accent-2)", label: "action",     icon: "⟳" },
  error:      { bg: "rgba(255,69,58,0.12)",   color: "var(--red)",      label: "error",      icon: "⚠" },
  report:     { bg: "rgba(255,214,10,0.12)",  color: "var(--yellow)",   label: "report",     icon: "◫" },
  checkpoint: { bg: "rgba(120,60,255,0.12)",  color: "var(--accent)",   label: "checkpoint", icon: "◈" },
  work:       { bg: "rgba(74,158,255,0.08)",  color: "var(--blue)",     label: "work",       icon: "◱" },
  summary:    { bg: "rgba(170,90,255,0.08)",  color: "var(--muted)",    label: "summary",    icon: "◪" },
};

const FALLBACK_TYPE: TypeStyle = { bg: "rgba(42,41,49,0.5)", color: "var(--muted)", label: "msg", icon: "◻" };

const ROSTER_ACTORS = ["clement", "claude", "codex", "athos"] as const;
const FILTER_TYPES  = ["message", "action", "result", "checkpoint", "error", "report", "summary"] as const;

const PROJECT_CTX: Record<string, { name: string; type: string; goal: string; href: string }> = {
  "rouge-pivoine": { name: "Rouge Pivoine", type: "Shopify", goal: "Push thème draft → GitHub", href: "/dashboard/projects/rouge-pivoine" },
  "placerr":       { name: "Placerr",       type: "Next.js", goal: "Choisir variante design v1-v6", href: "/dashboard/projects/placerr" },
  "athos":         { name: "ATHOS",         type: "ERP IA",  goal: "War Room v2 · Skill Registry", href: "/dashboard/projects" },
};

const CONTENT_COLLAPSE = 500;

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatTs(ts?: string): string {
  if (!ts) return "";
  try {
    return new Date(ts).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch { return ts; }
}

function formatRelative(ts?: string): string {
  if (!ts) return "jamais";
  try {
    const s = (Date.now() - new Date(ts).getTime()) / 1000;
    if (s < 10)    return "à l'instant";
    if (s < 60)    return `${Math.floor(s)}s`;
    if (s < 3600)  return `il y a ${Math.floor(s / 60)}min`;
    if (s < 86400) return `il y a ${Math.floor(s / 3600)}h`;
    return new Date(ts).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
  } catch { return ""; }
}

function actorOnlineStatus(lastTs?: string): { label: string; color: string; dot: string } {
  if (!lastTs) return { label: "absent", color: "var(--border)", dot: "○" };
  const s = (Date.now() - new Date(lastTs).getTime()) / 1000;
  if (s < 300)  return { label: "actif",      color: "var(--green)",  dot: "●" };
  if (s < 3600) return { label: "récent",     color: "var(--yellow)", dot: "●" };
  return              { label: "silencieux",  color: "var(--border)", dot: "○" };
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n) + "…" : s;
}

// ── War Room Header ─────────────────────────────────────────────────────────────

function WarRoomHeader({
  connected,
  activeEngine,
  orchestrating,
  totalMessages,
  visibleMessages,
  actorCount,
  warRoomMode,
  showSidebar,
  statusText,
  onToggleWarRoom,
  onToggleSidebar,
  onRefresh,
}: {
  connected: "ok" | "error" | "connecting";
  activeEngine?: string;
  orchestrating?: boolean;
  totalMessages: number;
  visibleMessages: number;
  actorCount: number;
  warRoomMode: boolean;
  showSidebar: boolean;
  statusText?: string;
  onToggleWarRoom: () => void;
  onToggleSidebar: () => void;
  onRefresh: () => void;
}) {
  const dotColor = connected === "ok" ? "var(--green)" : connected === "error" ? "var(--red)" : "var(--border)";

  return (
    <div style={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 10,
      flexWrap: "wrap",
      gap: 8,
      paddingBottom: 10,
      borderBottom: warRoomMode
        ? "1px solid rgba(120,60,255,0.4)"
        : "1px solid var(--border)",
    }}>
      {/* Left: title + meta */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <h1 style={{ fontSize: 22, fontWeight: 600, margin: 0, color: "var(--text)" }}>
              {warRoomMode ? "War Room" : "Room"}
            </h1>
            {warRoomMode && (
              <span style={{
                fontSize: 9, fontWeight: 700, letterSpacing: 1.5,
                color: "var(--accent)", border: "1px solid rgba(120,60,255,0.4)",
                padding: "1px 6px", borderRadius: 3, textTransform: "uppercase",
              }}>
                ◉ ACTIF
              </span>
            )}
          </div>
          <p style={{ color: "var(--muted)", fontSize: 12, margin: "2px 0 0" }}>
            {visibleMessages !== totalMessages
              ? `${visibleMessages}/${totalMessages} messages · ${actorCount} acteur${actorCount !== 1 ? "s" : ""}`
              : `${totalMessages} messages · ${actorCount} acteur${actorCount !== 1 ? "s" : ""} · live`
            }
          </p>
        </div>
      </div>

      {/* Right: controls */}
      <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
        {/* SSE status */}
        <div style={{
          display: "flex", alignItems: "center", gap: 7,
          padding: "4px 10px", background: "var(--surface-2)", borderRadius: 5, fontSize: 11,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: "50%", background: dotColor,
            boxShadow: connected === "ok" ? `0 0 4px ${dotColor}` : "none",
            flexShrink: 0, display: "inline-block",
          }} />
          <span style={{ color: "var(--muted)" }}>
            {connected === "connecting" ? "connexion…" : connected === "error" ? "hors ligne" :
             orchestrating ? "orchestration" : "live"}
          </span>
          {activeEngine && connected === "ok" && (
            <>
              <span style={{ color: "var(--border)" }}>·</span>
              <EngineBadge engine={activeEngine} />
            </>
          )}
        </div>

        {statusText && (
          <span style={{ fontSize: 11, color: "var(--muted)", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {statusText}
          </span>
        )}

        {/* War Room toggle */}
        <button
          onClick={onToggleWarRoom}
          title={warRoomMode ? "Quitter le mode War Room" : "Activer le mode War Room"}
          style={{
            fontSize: 11, padding: "4px 10px", borderRadius: 5, cursor: "pointer",
            border: warRoomMode ? "1px solid rgba(120,60,255,0.5)" : "1px solid var(--border)",
            background: warRoomMode ? "rgba(120,60,255,0.12)" : "none",
            color: warRoomMode ? "var(--accent)" : "var(--muted)",
            fontWeight: warRoomMode ? 600 : 400,
            transition: "all 0.15s",
          }}
        >
          ◉ War Room
        </button>

        {/* Sidebar toggle */}
        <button
          onClick={onToggleSidebar}
          title={showSidebar ? "Masquer le panneau" : "Afficher le panneau"}
          style={{
            fontSize: 11, padding: "4px 8px", borderRadius: 5, cursor: "pointer",
            border: "1px solid var(--border)", background: "none",
            color: showSidebar ? "var(--text)" : "var(--muted)",
          }}
        >
          {showSidebar ? "⊡" : "⊞"}
        </button>

        {/* Refresh */}
        <button
          onClick={onRefresh}
          title="Actualiser"
          style={{
            fontSize: 13, padding: "3px 8px", borderRadius: 5, cursor: "pointer",
            border: "1px solid var(--border)", background: "none", color: "var(--muted)",
          }}
        >
          ↻
        </button>

        {/* External link */}
        <a
          href="http://localhost:7474"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: 11, color: "var(--accent)",
            border: "1px solid var(--border)", padding: "4px 10px",
            borderRadius: 5, textDecoration: "none",
          }}
        >
          HUB →
        </a>
      </div>
    </div>
  );
}

// ── Room Filter Bar ─────────────────────────────────────────────────────────────

function RoomFilterBar({
  filterText,
  filterActors,
  filterTypes,
  totalThread,
  filteredCount,
  onFilterText,
  onToggleActor,
  onToggleType,
  onClearFilters,
}: {
  filterText: string;
  filterActors: Set<string>;
  filterTypes: Set<string>;
  totalThread: number;
  filteredCount: number;
  onFilterText: (v: string) => void;
  onToggleActor: (a: string) => void;
  onToggleType: (t: string) => void;
  onClearFilters: () => void;
}) {
  const hasFilters = filterText.trim() || filterActors.size > 0 || filterTypes.size > 0;

  const pillBase: React.CSSProperties = {
    display: "inline-flex", alignItems: "center", gap: 3,
    fontSize: 10, fontWeight: 600, letterSpacing: 0.3,
    padding: "2px 7px", borderRadius: 3, cursor: "pointer",
    border: "1px solid transparent", transition: "all 0.1s",
    userSelect: "none",
  };

  return (
    <div style={{
      marginBottom: 8, display: "flex", flexDirection: "column", gap: 6,
    }}>
      {/* Row 1: search + actor filters + count */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        {/* Search */}
        <input
          type="text"
          value={filterText}
          onChange={(e) => onFilterText(e.target.value)}
          placeholder="Rechercher dans le fil…"
          style={{
            flex: "1 1 160px", minWidth: 120, maxWidth: 260,
            background: "var(--surface-2)", border: "1px solid var(--border)",
            borderRadius: 4, padding: "3px 8px", fontSize: 11,
            color: "var(--text)", outline: "none",
          }}
        />

        {/* Actor pills */}
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {ROSTER_ACTORS.map((actor) => {
            const active = filterActors.has(actor);
            const color = ACTOR_COLOR[actor] ?? "var(--muted)";
            return (
              <span
                key={actor}
                onClick={() => onToggleActor(actor)}
                style={{
                  ...pillBase,
                  background: active ? `color-mix(in srgb, ${color} 15%, transparent)` : "var(--surface-2)",
                  border: `1px solid ${active ? `color-mix(in srgb, ${color} 35%, transparent)` : "var(--border)"}`,
                  color: active ? color : "var(--muted)",
                }}
              >
                <span style={{ fontSize: 6 }}>{active ? "●" : "○"}</span>
                {ACTOR_DISPLAY[actor] ?? actor}
              </span>
            );
          })}
        </div>

        {/* Results count + clear */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 10, color: hasFilters ? "var(--accent)" : "var(--border)", fontVariantNumeric: "tabular-nums" }}>
            {hasFilters ? `${filteredCount} / ${totalThread}` : `${totalThread} msgs`}
          </span>
          {hasFilters && (
            <button
              onClick={onClearFilters}
              style={{
                fontSize: 10, color: "var(--muted)", background: "none",
                border: "1px solid var(--border)", borderRadius: 3,
                padding: "1px 6px", cursor: "pointer",
              }}
            >
              × reset
            </button>
          )}
        </div>
      </div>

      {/* Row 2: type filters */}
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: 10, color: "var(--border)", marginRight: 2 }}>type</span>
        {FILTER_TYPES.map((type) => {
          const s = TYPE_STYLE[type] ?? FALLBACK_TYPE;
          const active = filterTypes.has(type);
          return (
            <span
              key={type}
              onClick={() => onToggleType(type)}
              style={{
                ...pillBase,
                background: active ? s.bg : "var(--surface-2)",
                border: `1px solid ${active ? s.color + "30" : "var(--border)"}`,
                color: active ? s.color : "var(--border)",
              }}
            >
              {s.icon} {type}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ── Session Context Panel ───────────────────────────────────────────────────────

function SessionContextPanel({
  connected,
  activeEngine,
  total,
  visible,
  athosStatus,
}: {
  connected: "ok" | "error" | "connecting";
  activeEngine?: string;
  total: number;
  visible: number;
  athosStatus?: AthosStatus;
}) {
  const dotColor = connected === "ok" ? "var(--green)" : connected === "error" ? "var(--red)" : "var(--border)";

  const row = (label: string, value: React.ReactNode, mono?: boolean) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "3px 0", borderBottom: "1px solid rgba(42,41,49,0.5)" }}>
      <span style={{ fontSize: 10, color: "var(--muted)" }}>{label}</span>
      <span style={{ fontSize: 10, color: "var(--text)", fontFamily: mono ? "monospace" : undefined }}>{value}</span>
    </div>
  );

  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, padding: "10px 12px" }}>
      <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 8 }}>
        Session
      </div>
      {row("SSE",
        <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: dotColor, boxShadow: connected === "ok" ? `0 0 3px ${dotColor}` : "none", display: "inline-block" }} />
          {connected === "ok" ? "connecté" : connected === "error" ? "hors ligne" : "connexion…"}
        </span>
      )}
      {activeEngine && row("Moteur", <EngineBadge engine={activeEngine} />)}
      {row("Msgs visibles", `${visible}`, true)}
      {total > visible && row("Total backend", `${total}`, true)}
      {athosStatus?.session && (
        <>
          {athosStatus.session.events > 0 && row("Événements", athosStatus.session.events, true)}
          {athosStatus.session.exchanges > 0 && row("Échanges", athosStatus.session.exchanges, true)}
          {athosStatus.session.actions > 0 && row("Actions", athosStatus.session.actions, true)}
        </>
      )}
      {athosStatus?.session?.checkpoint?.goal && (
        <div style={{ marginTop: 8, fontSize: 10, color: "var(--muted)", lineHeight: 1.4 }}>
          <span style={{ color: "var(--border)", marginRight: 4 }}>objectif</span>
          <span style={{ color: "var(--accent)" }}>{athosStatus.session.checkpoint.goal}</span>
        </div>
      )}
    </div>
  );
}

// ── Actor Roster Panel ──────────────────────────────────────────────────────────

function ActorRosterPanel({
  actorStats,
  filterActors,
  onToggleActor,
}: {
  actorStats: Record<string, { lastTs?: string; count: number }>;
  filterActors: Set<string>;
  onToggleActor: (a: string) => void;
}) {
  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, padding: "10px 12px" }}>
      <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase", marginBottom: 8 }}>
        Acteurs
      </div>
      {ROSTER_ACTORS.map((actor) => {
        const stats = actorStats[actor];
        const s = actorOnlineStatus(stats?.lastTs);
        const color = ACTOR_COLOR[actor] ?? "var(--muted)";
        const isFiltered = filterActors.has(actor);
        const inThread = !!stats && stats.count > 0;

        return (
          <div
            key={actor}
            onClick={() => onToggleActor(actor)}
            title={`${stats?.count ?? 0} message(s) · ${stats?.lastTs ? formatRelative(stats.lastTs) : "absent"}`}
            style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "4px 6px", borderRadius: 4, marginBottom: 2, cursor: "pointer",
              background: isFiltered ? `color-mix(in srgb, ${color} 10%, transparent)` : "transparent",
              border: `1px solid ${isFiltered ? `color-mix(in srgb, ${color} 25%, transparent)` : "transparent"}`,
              transition: "all 0.1s",
              opacity: inThread ? 1 : 0.4,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 7, color: s.color }}>{s.dot}</span>
              <span style={{ fontSize: 11, color: inThread ? color : "var(--border)", fontWeight: 600 }}>
                {ACTOR_DISPLAY[actor] ?? actor}
              </span>
              {stats?.count != null && stats.count > 0 && (
                <span style={{ fontSize: 9, color: "var(--border)", fontVariantNumeric: "tabular-nums" }}>
                  {stats.count}
                </span>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              {inThread && (
                <span style={{ fontSize: 9, color: s.color }}>{s.label}</span>
              )}
              {stats?.lastTs && (
                <span style={{ fontSize: 9, color: "var(--border)" }}>{formatRelative(stats.lastTs)}</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Project Context Card ────────────────────────────────────────────────────────

function ProjectContextCard({
  selectedProject,
  onSelectProject,
}: {
  selectedProject: string;
  onSelectProject: (p: string) => void;
}) {
  const proj = PROJECT_CTX[selectedProject];

  return (
    <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, padding: "10px 12px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.5, color: "var(--muted)", textTransform: "uppercase" }}>
          Projet actif
        </div>
        <span style={{ fontSize: 9, color: "var(--yellow)", border: "1px solid rgba(255,214,10,0.3)", padding: "1px 5px", borderRadius: 2 }}>
          prototype
        </span>
      </div>

      <select
        value={selectedProject}
        onChange={(e) => onSelectProject(e.target.value)}
        style={{
          width: "100%", background: "var(--surface-2)", border: "1px solid var(--border)",
          borderRadius: 4, padding: "4px 6px", fontSize: 11, color: "var(--text)",
          marginBottom: proj ? 10 : 0, cursor: "pointer", outline: "none",
        }}
      >
        <option value="none">— Aucun projet —</option>
        {Object.entries(PROJECT_CTX).map(([key, p]) => (
          <option key={key} value={key}>{p.name}</option>
        ))}
      </select>

      {proj && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text)" }}>{proj.name}</span>
            <span style={{ fontSize: 9, color: "var(--muted)", background: "var(--surface-2)", padding: "1px 5px", borderRadius: 3 }}>
              {proj.type}
            </span>
          </div>
          <div style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.4, marginBottom: 8 }}>
            <span style={{ color: "var(--accent)", marginRight: 4 }}>→</span>
            {proj.goal}
          </div>
          <Link
            href={proj.href}
            style={{
              fontSize: 10, color: "var(--accent)", textDecoration: "none",
              display: "inline-flex", alignItems: "center", gap: 4,
              padding: "3px 8px", border: "1px solid rgba(120,60,255,0.3)",
              borderRadius: 4, background: "rgba(120,60,255,0.06)",
            }}
          >
            Fiche projet →
          </Link>
        </div>
      )}
    </div>
  );
}

// ── Room Message ────────────────────────────────────────────────────────────────

function RoomMessage({ entry, highlight }: { entry: RoomEntry; highlight?: string }) {
  const [expanded, setExpanded] = useState(false);

  const actorKey    = entry.actor ?? "";
  const actorColor  = ACTOR_COLOR[actorKey] ?? "var(--muted)";
  const displayActor= (ACTOR_LABEL[actorKey] ?? actorKey) || "?";
  const typeStyle   = TYPE_STYLE[entry.type ?? ""] ?? FALLBACK_TYPE;
  const ts          = formatTs(entry.ts);
  const isClement   = actorKey === "clement";
  const isError     = entry.type === "error";
  const isCheckpoint= entry.type === "checkpoint";
  const isReport    = entry.type === "report";
  const isSummary   = entry.type === "summary";
  const isLong      = (entry.content?.length ?? 0) > CONTENT_COLLAPSE;
  const displayContent = isLong && !expanded
    ? entry.content!.slice(0, CONTENT_COLLAPSE) + "…"
    : (entry.content ?? "");

  const contentColor = isError ? "var(--red)" : isCheckpoint ? "var(--accent)" : "var(--text)";

  const isHighlighted = !!highlight && (
    entry.content?.toLowerCase().includes(highlight.toLowerCase()) ||
    displayActor.toLowerCase().includes(highlight.toLowerCase())
  );

  // ── Error / Blocker callout ──────────────────────────────────────────────────
  if (isError) {
    return (
      <div style={{
        padding: "10px 14px", marginBottom: 1,
        background: "rgba(255,69,58,0.06)",
        borderLeft: "3px solid var(--red)",
        borderBottom: "1px solid var(--border)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "var(--red)", letterSpacing: 0.8, textTransform: "uppercase" }}>
            ⚠ Erreur · blocage
          </span>
          <span style={{ fontSize: 9, color: "var(--border)" }}>{ts}</span>
          <span style={{ fontSize: 9, color: "var(--muted)", marginLeft: "auto" }}>{displayActor}</span>
        </div>
        <div style={{ fontSize: 12, color: "var(--red)", lineHeight: 1.5, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {displayContent}
        </div>
        {isLong && (
          <button onClick={() => setExpanded(!expanded)} style={{ marginTop: 5, fontSize: 10, color: "var(--red)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            {expanded ? "▲ réduire" : "▼ voir tout"}
          </button>
        )}
      </div>
    );
  }

  // ── Checkpoint ───────────────────────────────────────────────────────────────
  if (isCheckpoint) {
    return (
      <div style={{
        padding: "10px 14px", marginBottom: 1,
        background: "rgba(120,60,255,0.05)",
        borderLeft: "3px solid var(--accent)",
        borderBottom: "1px solid var(--border)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "var(--accent)", letterSpacing: 0.8, textTransform: "uppercase" }}>
            ◈ Checkpoint
          </span>
          <span style={{ fontSize: 9, color: "var(--border)" }}>{ts}</span>
          <span style={{ fontSize: 9, color: "var(--muted)", marginLeft: "auto" }}>{displayActor}</span>
        </div>
        <div style={{ fontSize: 12, color: "var(--accent)", lineHeight: 1.5, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
          {displayContent}
        </div>
        {isLong && (
          <button onClick={() => setExpanded(!expanded)} style={{ marginTop: 5, fontSize: 10, color: "var(--accent)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            {expanded ? "▲ réduire" : "▼ voir tout"}
          </button>
        )}
      </div>
    );
  }

  // ── Report / Summary — collapsed card ────────────────────────────────────────
  if (isReport || isSummary) {
    return (
      <div
        style={{
          padding: "8px 14px", marginBottom: 1,
          background: isHighlighted ? "rgba(255,214,10,0.04)" : "rgba(170,90,255,0.04)",
          borderLeft: "3px solid rgba(255,214,10,0.4)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: isLong ? 4 : 0 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "var(--yellow)", letterSpacing: 0.8, textTransform: "uppercase" }}>
            {typeStyle.icon} {isSummary ? "Résumé" : "Rapport"}
          </span>
          <span style={{ fontSize: 9, color: "var(--border)" }}>{ts}</span>
          <span style={{ fontSize: 9, color: "var(--muted)", marginLeft: "auto" }}>{displayActor}</span>
          <button onClick={() => setExpanded(!expanded)} style={{ fontSize: 10, color: "var(--muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            {expanded ? "▲" : "▼"}
          </button>
        </div>
        {expanded && (
          <div style={{ fontSize: 11, color: "var(--text)", lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word", marginTop: 4, opacity: 0.85 }}>
            {entry.content ?? ""}
          </div>
        )}
        {!expanded && (
          <div style={{ fontSize: 10, color: "var(--muted)", fontStyle: "italic" }}>
            {truncate(entry.content ?? "", 120)}
          </div>
        )}
      </div>
    );
  }

  // ── Standard message ──────────────────────────────────────────────────────────
  return (
    <div style={{
      padding: "7px 12px 7px 0", marginBottom: 1,
      borderBottom: "1px solid var(--border)",
      display: "flex", gap: 0,
      background: isHighlighted
        ? "rgba(255,214,10,0.04)"
        : isClement ? "rgba(74,158,255,0.03)" : "transparent",
      borderLeft: `3px solid ${isClement ? "var(--blue)" : actorColor}`,
    }}>
      {/* Actor col */}
      <div style={{ minWidth: 72, flexShrink: 0, paddingLeft: 10, paddingRight: 4 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: actorColor, letterSpacing: 0.3 }}>
          {displayActor}
        </div>
        <div style={{ fontSize: 9, color: "var(--border)", marginTop: 1 }}>{ts}</div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0, paddingRight: 10 }}>
        <div style={{
          fontSize: 12, color: contentColor, lineHeight: 1.55,
          whiteSpace: "pre-wrap", wordBreak: "break-word",
          opacity: actorKey === "athos" && entry.type === "action" ? 0.7 : 1,
        }}>
          {displayContent}
        </div>
        {isLong && (
          <button onClick={() => setExpanded(!expanded)} style={{ marginTop: 3, fontSize: 10, color: "var(--muted)", background: "none", border: "none", cursor: "pointer", padding: 0, letterSpacing: 0.3 }}>
            {expanded ? "▲ réduire" : `▼ voir tout (${entry.content!.length} car.)`}
          </button>
        )}
        {entry.task_id && (
          <div style={{ marginTop: 3, fontSize: 9, color: "var(--border)", fontFamily: "monospace" }}>
            task:{truncate(entry.task_id, 14)}
          </div>
        )}
      </div>

      {/* Type badge */}
      <div style={{ flexShrink: 0, paddingTop: 1, paddingRight: 10 }}>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 3,
          fontSize: 9, padding: "2px 5px", borderRadius: 3,
          background: typeStyle.bg, color: typeStyle.color,
          fontWeight: 600, letterSpacing: 0.3,
        }}>
          {typeStyle.icon} {typeStyle.label}
        </span>
      </div>
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────────────────

export default function RoomClient({
  initialThread,
  totalMessages,
  athosStatus,
}: {
  initialThread: RoomEntry[];
  totalMessages: number;
  athosStatus?: AthosStatus;
}) {
  const [thread,         setThread]         = useState<RoomEntry[]>(initialThread);
  const [input,          setValue]          = useState("");
  const [sending,        setSending]        = useState(false);
  const [statusText,     setStatusText]     = useState("");
  const [total,          setTotal]          = useState(totalMessages);
  const [sseState,       setSseState]       = useState<"connecting"|"ok"|"error">("connecting");
  const [activeEngine,   setActiveEngine]   = useState<string | undefined>(athosStatus?.engine);
  const [warRoomMode,    setWarRoomMode]    = useState(false);
  const [showSidebar,    setShowSidebar]    = useState(true);
  const [selectedProject,setSelectedProject]= useState("none");
  const [filterText,     setFilterText]     = useState("");
  const [filterActors,   setFilterActors]   = useState<Set<string>>(new Set());
  const [filterTypes,    setFilterTypes]    = useState<Set<string>>(new Set());

  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef     = useRef<EventSource | null>(null);

  // ── Computed ─────────────────────────────────────────────────────────────────

  const filteredThread = useMemo(() => {
    let r = thread;
    if (filterText.trim()) {
      const q = filterText.toLowerCase();
      r = r.filter(e =>
        e.content?.toLowerCase().includes(q) ||
        (ACTOR_LABEL[e.actor ?? ""] ?? e.actor ?? "").toLowerCase().includes(q)
      );
    }
    if (filterActors.size > 0) {
      r = r.filter(e => {
        const a = e.actor ?? "";
        return filterActors.has(a) || filterActors.has(ACTOR_LABEL[a] ?? a);
      });
    }
    if (filterTypes.size > 0) {
      r = r.filter(e => filterTypes.has(e.type ?? ""));
    }
    return r;
  }, [thread, filterText, filterActors, filterTypes]);

  const actorStats = useMemo(() => {
    const stats: Record<string, { lastTs?: string; count: number }> = {};
    for (const entry of thread) {
      const raw   = entry.actor ?? "unknown";
      const actor = ACTOR_LABEL[raw] ?? raw;
      if (!stats[actor]) stats[actor] = { count: 0 };
      stats[actor].count++;
      if (!stats[actor].lastTs || (entry.ts && entry.ts > (stats[actor].lastTs ?? ""))) {
        stats[actor].lastTs = entry.ts;
      }
      // Also index by raw key for ROSTER_ACTORS lookup
      if (raw !== actor) {
        if (!stats[raw]) stats[raw] = { count: 0 };
        stats[raw].count = stats[actor].count;
        stats[raw].lastTs = stats[actor].lastTs;
      }
    }
    return stats;
  }, [thread]);

  const actorCount = useMemo(() => {
    const seen = new Set<string>();
    for (const e of thread) {
      const raw   = e.actor ?? "";
      const actor = ACTOR_LABEL[raw] ?? raw;
      if (actor) seen.add(actor);
    }
    return seen.size;
  }, [thread]);

  const hasFilters = filterText.trim().length > 0 || filterActors.size > 0 || filterTypes.size > 0;

  // ── Refresh ───────────────────────────────────────────────────────────────────

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

  // ── SSE ───────────────────────────────────────────────────────────────────────

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
      es.addEventListener("session_event", () => { if (!cancelled) refresh(); });
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

  // Fallback poll
  useEffect(() => {
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, [refresh]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (!hasFilters) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread.length, hasFilters]);

  // ── Send ──────────────────────────────────────────────────────────────────────

  async function send() {
    const content = input.trim();
    if (!content || sending) return;
    setSending(true);
    setValue("");
    setStatusText("Envoi…");
    try {
      const res = await fetch("/api/athos-proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: "/api/message",
          payload: { actor: "clement", content, type: "message", task_id: `room-${Date.now()}` },
        }),
      });
      const data = await res.json();
      if (data.auto_work?.scheduled)     setStatusText("Orchestration ATHOS en cours…");
      else if (data.auto_response?.scheduled) setStatusText("Engine en cours de réponse…");
      else                                    setStatusText("Message ajouté.");
      await refresh();
      setTimeout(() => { refresh(); setStatusText(""); }, 3000);
    } catch (e) {
      setStatusText(`Erreur: ${String(e)}`);
    } finally {
      setSending(false);
    }
  }

  // ── Filter helpers ────────────────────────────────────────────────────────────

  function toggleActor(actor: string) {
    setFilterActors(prev => {
      const next = new Set(prev);
      if (next.has(actor)) next.delete(actor); else next.add(actor);
      return next;
    });
  }

  function toggleType(type: string) {
    setFilterTypes(prev => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type); else next.add(type);
      return next;
    });
  }

  function clearFilters() {
    setFilterText("");
    setFilterActors(new Set());
    setFilterTypes(new Set());
  }

  const orchestrating = statusText.includes("cours");

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>

      {/* War Room Header */}
      <WarRoomHeader
        connected={sseState}
        activeEngine={activeEngine}
        orchestrating={orchestrating}
        totalMessages={total}
        visibleMessages={filteredThread.length}
        actorCount={actorCount}
        warRoomMode={warRoomMode}
        showSidebar={showSidebar}
        statusText={statusText}
        onToggleWarRoom={() => setWarRoomMode(p => !p)}
        onToggleSidebar={() => setShowSidebar(p => !p)}
        onRefresh={refresh}
      />

      {/* Main content: thread + sidebar */}
      <div style={{ flex: 1, display: "flex", gap: 12, overflow: "hidden", minHeight: 0 }}>

        {/* Left: filter bar + thread + input */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

          {/* Filter bar */}
          <RoomFilterBar
            filterText={filterText}
            filterActors={filterActors}
            filterTypes={filterTypes}
            totalThread={thread.length}
            filteredCount={filteredThread.length}
            onFilterText={setFilterText}
            onToggleActor={toggleActor}
            onToggleType={toggleType}
            onClearFilters={clearFilters}
          />

          {/* Thread */}
          <div style={{
            flex: 1, background: "var(--surface)",
            border: warRoomMode
              ? "1px solid rgba(120,60,255,0.35)"
              : "1px solid var(--border)",
            borderRadius: 8, overflowY: "auto", marginBottom: 10,
            boxShadow: warRoomMode ? "0 0 0 1px rgba(120,60,255,0.15), 0 0 40px rgba(120,60,255,0.06)" : "none",
            transition: "box-shadow 0.3s, border-color 0.3s",
          }}>
            {/* Pagination notice */}
            {total > thread.length && (
              <div style={{
                padding: "7px 14px", borderBottom: "1px solid var(--border)",
                background: "rgba(255,214,10,0.04)", fontSize: 10,
                color: "var(--yellow)", display: "flex", gap: 8, alignItems: "center",
              }}>
                <span>◫</span>
                <span>{thread.length} derniers messages affichés sur {total} total · pagination backend à prévoir</span>
              </div>
            )}

            {filteredThread.length === 0 ? (
              <div style={{ padding: 48, textAlign: "center" }}>
                <div style={{ fontSize: 24, color: "var(--border)", marginBottom: 10 }}>◉</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--muted)", marginBottom: 6 }}>
                  {thread.length === 0 ? "Room vide" : "Aucun résultat"}
                </div>
                <div style={{ fontSize: 11, color: "var(--border)", maxWidth: 260, margin: "0 auto", lineHeight: 1.5 }}>
                  {thread.length === 0
                    ? sseState === "error"
                      ? "Connexion SSE hors ligne — ATHOS HUB inaccessible. Vérifier :7474."
                      : "Envoyer un message pour démarrer une session ATHOS."
                    : "Aucun message ne correspond aux filtres actifs."}
                </div>
                {hasFilters && (
                  <button
                    onClick={clearFilters}
                    style={{
                      marginTop: 12, fontSize: 11, color: "var(--accent)",
                      background: "none", border: "1px solid rgba(120,60,255,0.3)",
                      borderRadius: 4, padding: "4px 12px", cursor: "pointer",
                    }}
                  >
                    Effacer les filtres
                  </button>
                )}
              </div>
            ) : (
              filteredThread.map((entry) => (
                <RoomMessage
                  key={entry.id ?? entry.ts}
                  entry={entry}
                  highlight={filterText.trim() || undefined}
                />
              ))
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{
            display: "flex", gap: 8,
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 8, padding: "8px 12px",
          }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              placeholder={warRoomMode ? "Commande War Room…" : "Message dans le fil ATHOS Room…"}
              disabled={sending}
              style={{
                flex: 1, background: "none", border: "none",
                outline: "none", color: "var(--text)", fontSize: 13, padding: "4px 0",
              }}
            />
            <button
              onClick={send}
              disabled={sending || !input.trim()}
              style={{
                padding: "6px 16px",
                background: input.trim() && !sending ? "var(--accent)" : "var(--surface-2)",
                color: input.trim() && !sending ? "#fff" : "var(--muted)",
                border: "none", borderRadius: 6, fontSize: 12,
                cursor: input.trim() && !sending ? "pointer" : "default",
                transition: "all 0.15s",
              }}
            >
              {sending ? "…" : "Envoyer"}
            </button>
          </div>
        </div>

        {/* Right: sidebar */}
        {showSidebar && (
          <div style={{
            width: 254, flexShrink: 0, display: "flex", flexDirection: "column",
            gap: 8, overflowY: "auto",
          }}>
            <SessionContextPanel
              connected={sseState}
              activeEngine={activeEngine}
              total={total}
              visible={thread.length}
              athosStatus={athosStatus}
            />
            <ActorRosterPanel
              actorStats={actorStats}
              filterActors={filterActors}
              onToggleActor={toggleActor}
            />
            <ProjectContextCard
              selectedProject={selectedProject}
              onSelectProject={setSelectedProject}
            />
          </div>
        )}
      </div>
    </div>
  );
}
