"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard/hub", label: "Vue Centrale", icon: "◈", group: null },
  { href: "/dashboard/room", label: "Room", icon: "◉", group: "Opérations" },
  { href: "/dashboard/agents", label: "Agents IA", icon: "⬡", group: "Opérations" },
  { href: "/dashboard/automations", label: "Automations", icon: "⟳", group: "Opérations" },
  { href: "/dashboard/reports", label: "Rapports", icon: "◫", group: "Opérations" },
  { href: "#", label: "Sites & Projets", icon: "◱", group: "Projets", soon: true },
  { href: "#", label: "SEO Analytics", icon: "◲", group: "Projets", soon: true },
  { href: "#", label: "Performance", icon: "◳", group: "Projets", soon: true },
  { href: "#", label: "Finances", icon: "◻", group: "Business", soon: true },
  { href: "#", label: "Commandes", icon: "◼", group: "Business", soon: true },
  { href: "#", label: "CRM / Clients", icon: "◾", group: "Business", soon: true },
  { href: "#", label: "Roadmap", icon: "◪", group: "Système", soon: true },
  { href: "#", label: "Alertes", icon: "◈", group: "Système", soon: true },
  { href: "#", label: "Paramètres", icon: "⊙", group: "Système", soon: true },
];

export default function Sidebar() {
  const path = usePathname();
  let currentGroup: string | null = undefined as unknown as null;

  return (
    <aside
      style={{
        width: 220,
        minWidth: 220,
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        padding: "16px 0",
        gap: 2,
        overflowY: "auto",
      }}
    >
      <div style={{ padding: "0 16px 16px", borderBottom: "1px solid var(--border)", marginBottom: 8 }}>
        <span style={{ fontSize: 11, letterSpacing: 2, color: "var(--accent)", fontWeight: 700 }}>
          A.T.H.O.S.
        </span>
      </div>

      {NAV.map((item) => {
        const showGroup = item.group !== currentGroup;
        if (showGroup) currentGroup = item.group;
        const active = path === item.href;

        return (
          <div key={item.href + item.label}>
            {showGroup && item.group && (
              <div
                style={{
                  padding: "12px 16px 4px",
                  fontSize: 10,
                  letterSpacing: 1.5,
                  color: "var(--muted)",
                  textTransform: "uppercase",
                  fontWeight: 600,
                }}
              >
                {item.group}
              </div>
            )}
            <Link
              href={item.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "7px 16px",
                fontSize: 13,
                color: active ? "var(--text)" : item.soon ? "var(--border)" : "var(--muted)",
                background: active ? "var(--surface-2)" : "transparent",
                borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                textDecoration: "none",
                cursor: item.soon ? "default" : "pointer",
                pointerEvents: item.soon ? "none" : "auto",
                transition: "all 0.15s",
              }}
            >
              <span style={{ fontSize: 12, opacity: item.soon ? 0.3 : 1 }}>{item.icon}</span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.soon && (
                <span
                  style={{
                    fontSize: 9,
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    color: "var(--muted)",
                    padding: "1px 5px",
                    borderRadius: 3,
                    letterSpacing: 0.5,
                  }}
                >
                  SOON
                </span>
              )}
            </Link>
          </div>
        );
      })}
    </aside>
  );
}
