import React from "react";

// ── Card ─────────────────────────────────────────────────────────────────────

export function Card({
  title,
  children,
  noPad = false,
}: {
  title?: string;
  children: React.ReactNode;
  noPad?: boolean;
}) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        overflow: "hidden",
      }}
    >
      {title && (
        <div
          style={{
            padding: "11px 16px",
            borderBottom: "1px solid var(--border)",
            fontSize: 11,
            letterSpacing: 1.2,
            color: "var(--muted)",
            textTransform: "uppercase",
            fontWeight: 600,
          }}
        >
          {title}
        </div>
      )}
      <div style={noPad ? undefined : { padding: 16 }}>{children}</div>
    </div>
  );
}

// ── StatCard ─────────────────────────────────────────────────────────────────

export function StatCard({
  label,
  value,
  sub,
  color,
  size = "md",
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
  size?: "sm" | "md" | "lg";
}) {
  const fs = size === "lg" ? 28 : size === "sm" ? 16 : 22;
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "14px 16px",
      }}
    >
      <div style={{ fontSize: fs, fontWeight: 700, color: color ?? "var(--text)", lineHeight: 1.1 }}>
        {value}
      </div>
      <div
        style={{
          fontSize: 11,
          color: "var(--muted)",
          textTransform: "uppercase",
          letterSpacing: 1,
          marginTop: 5,
        }}
      >
        {label}
      </div>
      {sub && (
        <div style={{ fontSize: 10, color: "var(--border)", marginTop: 3 }}>{sub}</div>
      )}
    </div>
  );
}

// ── Badge ────────────────────────────────────────────────────────────────────

type BadgeVariant = "green" | "red" | "yellow" | "blue" | "accent" | "muted" | "border";

const BADGE_COLORS: Record<BadgeVariant, string> = {
  green: "var(--green)",
  red: "var(--red)",
  yellow: "var(--yellow)",
  blue: "var(--blue)",
  accent: "var(--accent)",
  muted: "var(--muted)",
  border: "var(--border)",
};

export function Badge({
  label,
  variant = "muted",
  dot = false,
}: {
  label: string;
  variant?: BadgeVariant;
  dot?: boolean;
}) {
  const color = BADGE_COLORS[variant];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "2px 8px",
        borderRadius: 20,
        fontSize: 11,
        fontWeight: 500,
        background: `color-mix(in srgb, ${color} 14%, transparent)`,
        color,
        border: `1px solid color-mix(in srgb, ${color} 28%, transparent)`,
        whiteSpace: "nowrap",
      }}
    >
      {dot && <span style={{ fontSize: 7, lineHeight: 1 }}>●</span>}
      {label}
    </span>
  );
}

// ── Engine badge ─────────────────────────────────────────────────────────────

const ENGINE_VARIANT: Record<string, BadgeVariant> = {
  claude: "accent",
  claude_code: "accent",
  codex: "green",
  chatgpt_plus: "green",
  athos: "blue",
  ollama: "muted",
};

export function EngineBadge({ engine }: { engine: string }) {
  const variant = ENGINE_VARIANT[engine] ?? "border";
  const label = engine.replace(/_/g, " ");
  return <Badge label={label} variant={variant} dot />;
}

// ── SectionLabel ──────────────────────────────────────────────────────────────

export function SectionLabel({ children, count }: { children: React.ReactNode; count?: number }) {
  return (
    <div
      style={{
        fontSize: 11,
        letterSpacing: 1.5,
        color: "var(--muted)",
        textTransform: "uppercase",
        fontWeight: 600,
        marginBottom: 12,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {children}
      {count !== undefined && (
        <span style={{ color: "var(--border)", fontSize: 10 }}>({count})</span>
      )}
    </div>
  );
}

// ── DataRow ───────────────────────────────────────────────────────────────────

export function DataRow({
  label,
  value,
  mono = false,
  color,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  color?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        gap: 12,
        padding: "7px 0",
        borderBottom: "1px solid var(--border)",
        fontSize: 13,
        flexWrap: "wrap",
      }}
    >
      <span style={{ color: "var(--muted)", flexShrink: 0 }}>{label}</span>
      <span
        style={{
          color: color ?? "var(--text)",
          fontFamily: mono ? "monospace" : undefined,
          fontSize: mono ? 12 : undefined,
          textAlign: "right",
          wordBreak: "break-all",
        }}
      >
        {value}
      </span>
    </div>
  );
}

// ── MockBanner ────────────────────────────────────────────────────────────────

export function MockBanner({ message }: { message?: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        background: "rgba(255,214,10,0.08)",
        border: "1px solid rgba(255,214,10,0.25)",
        borderRadius: 6,
        padding: "8px 14px",
        marginBottom: 20,
        fontSize: 12,
        color: "var(--yellow)",
      }}
    >
      <span style={{ fontSize: 14 }}>⚠</span>
      <span>
        <strong>DONNÉES MOCK</strong>
        {message ? ` — ${message}` : " — Ces données sont des exemples. Connecter les sources réelles pour voir les vraies valeurs."}
      </span>
    </div>
  );
}

// ── BarChart (CSS) ────────────────────────────────────────────────────────────

export function BarChart({
  data,
  height = 120,
  color = "var(--accent)",
}: {
  data: { label: string; value: number }[];
  height?: number;
  color?: string;
}) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height }}>
      {data.map((d) => {
        const pct = (d.value / max) * 100;
        return (
          <div key={d.label} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4, height: "100%" }}>
            <div style={{ flex: 1, display: "flex", alignItems: "flex-end", width: "100%" }}>
              <div
                style={{
                  width: "100%",
                  height: `${pct}%`,
                  minHeight: 2,
                  background: color,
                  borderRadius: "3px 3px 0 0",
                  opacity: 0.85,
                  transition: "height 0.3s ease",
                }}
              />
            </div>
            <div style={{ fontSize: 9, color: "var(--border)", whiteSpace: "nowrap" }}>{d.label}</div>
          </div>
        );
      })}
    </div>
  );
}

// ── Gauge ─────────────────────────────────────────────────────────────────────

export function Gauge({ value, max = 100, color }: { value: number; max?: number; color?: string }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  const c = color ?? (pct >= 80 ? "var(--green)" : pct >= 50 ? "var(--yellow)" : "var(--red)");
  return (
    <div>
      <div
        style={{
          height: 6,
          background: "var(--surface-2)",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: c,
            borderRadius: 3,
            transition: "width 0.4s ease",
          }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 10, color: "var(--muted)" }}>
        <span>{value}</span>
        <span>{pct}%</span>
      </div>
    </div>
  );
}

// ── PageHeader ────────────────────────────────────────────────────────────────

export function PageHeader({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        marginBottom: 24,
        flexWrap: "wrap",
        gap: 12,
      }}
    >
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, margin: "0 0 4px" }}>{title}</h1>
        {subtitle && (
          <p style={{ color: "var(--muted)", fontSize: 13, margin: 0 }}>{subtitle}</p>
        )}
      </div>
      {children && (
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
          {children}
        </div>
      )}
    </div>
  );
}

// ── RealityBadge ─────────────────────────────────────────────────────────────

type RealityLevel = "RÉEL" | "MOCK" | "MIXTE" | "STATIQUE" | "CODEX";

const REALITY_VARIANT: Record<RealityLevel, BadgeVariant> = {
  "RÉEL":     "green",
  "MOCK":     "yellow",
  "MIXTE":    "blue",
  "STATIQUE": "muted",
  "CODEX":    "border",
};

export function RealityBadge({ level }: { level: RealityLevel }) {
  return <Badge label={level} variant={REALITY_VARIANT[level]} />;
}

// ── EmptyPanel ────────────────────────────────────────────────────────────────

export function EmptyPanel({
  icon = "◱",
  label,
  detail,
}: {
  icon?: string;
  label: string;
  detail?: string;
}) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "32px 24px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 20, color: "var(--border)", marginBottom: 8 }}>{icon}</div>
      <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 4 }}>{label}</div>
      {detail && <div style={{ fontSize: 11, color: "var(--border)" }}>{detail}</div>}
    </div>
  );
}

// ── InsetNotice ───────────────────────────────────────────────────────────────

export function InsetNotice({
  icon = "◱",
  text,
  detail,
  variant = "muted",
}: {
  icon?: string;
  text: string;
  detail?: string;
  variant?: "muted" | "yellow" | "blue" | "green" | "red";
}) {
  const color = variant === "yellow" ? "var(--yellow)"
    : variant === "blue" ? "var(--blue)"
    : variant === "green" ? "var(--green)"
    : variant === "red" ? "var(--red)"
    : "var(--muted)";
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 8,
        padding: "8px 12px",
        borderRadius: 5,
        background: `color-mix(in srgb, ${color} 8%, transparent)`,
        border: `1px solid color-mix(in srgb, ${color} 20%, transparent)`,
        marginBottom: 12,
      }}
    >
      <span style={{ fontSize: 12, color, flexShrink: 0, marginTop: 1 }}>{icon}</span>
      <div>
        <span style={{ fontSize: 12, color }}>{text}</span>
        {detail && (
          <span style={{ fontSize: 11, color: "var(--muted)", marginLeft: 6 }}>{detail}</span>
        )}
      </div>
    </div>
  );
}

// ── StatusDot ─────────────────────────────────────────────────────────────────

export function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  const color = ok ? "var(--green)" : "var(--red)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: color,
          boxShadow: `0 0 4px ${color}`,
          flexShrink: 0,
          display: "inline-block",
        }}
      />
      <span style={{ color: ok ? "var(--text)" : "var(--muted)" }}>{label}</span>
    </div>
  );
}
