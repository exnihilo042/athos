"use client";
import { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  group: string | null;
  soon?: boolean;
}

const NAV: NavItem[] = [
  { href: "/dashboard/hub",         label: "Vue Centrale",  icon: "◈", group: null },
  { href: "/dashboard/room",        label: "Room",          icon: "◉", group: "Opérations" },
  { href: "/dashboard/agents",      label: "Agents IA",     icon: "⬡", group: "Opérations" },
  { href: "/dashboard/automations", label: "Automations",   icon: "⟳", group: "Opérations" },
  { href: "/dashboard/reports",     label: "Rapports",      icon: "◫", group: "Opérations" },
  { href: "/dashboard/alerts",      label: "Alertes",       icon: "⚠", group: "Système" },
  { href: "/dashboard/projects",  label: "Sites & Projets", icon: "◱", group: "Projets" },
  { href: "/dashboard/seo",       label: "SEO Analytics",   icon: "◲", group: "Projets" },
  { href: "/dashboard/performance", label: "Performance",      icon: "◳", group: "Projets" },
  { href: "/dashboard/finances",    label: "Finances",         icon: "◻", group: "Business" },
  { href: "/dashboard/commandes",   label: "Commandes",        icon: "◼", group: "Business" },
  { href: "/dashboard/crm",         label: "CRM / Clients",    icon: "◾", group: "Business" },
  { href: "/dashboard/roadmap",   label: "Roadmap",          icon: "◪", group: "Système" },
  { href: "/dashboard/settings",  label: "Paramètres",       icon: "⊙", group: "Système" },
];

function SidebarContent({ onNav }: { onNav?: () => void }) {
  const path = usePathname();
  let currentGroup: string | null = undefined as unknown as null;

  return (
    <>
      <div style={{ padding: "16px 16px 14px", borderBottom: "1px solid var(--border)" }}>
        <span style={{ fontSize: 11, letterSpacing: 2, color: "var(--accent)", fontWeight: 700 }}>
          A.T.H.O.S.
        </span>
      </div>
      <div style={{ padding: "8px 0", flex: 1 }}>
        {NAV.map((item) => {
          const showGroup = item.group !== currentGroup;
          if (showGroup) currentGroup = item.group;
          const active = path === item.href;
          return (
            <div key={item.href + item.label}>
              {showGroup && item.group && (
                <div style={{ padding: "10px 16px 3px", fontSize: 10, letterSpacing: 1.5, color: "var(--border)", textTransform: "uppercase", fontWeight: 600 }}>
                  {item.group}
                </div>
              )}
              <Link
                href={item.href}
                onClick={item.soon ? undefined : onNav}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "8px 16px", fontSize: 13,
                  color: active ? "var(--text)" : item.soon ? "var(--border)" : "var(--muted)",
                  background: active ? "var(--surface-2)" : "transparent",
                  borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                  textDecoration: "none",
                  cursor: item.soon ? "default" : "pointer",
                  pointerEvents: item.soon ? "none" : "auto",
                  transition: "background 0.12s, color 0.12s",
                }}
              >
                <span style={{ fontSize: 12, opacity: item.soon ? 0.3 : 1, minWidth: 14 }}>{item.icon}</span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.soon && (
                  <span style={{ fontSize: 9, background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--border)", padding: "1px 4px", borderRadius: 3 }}>
                    SOON
                  </span>
                )}
              </Link>
            </div>
          );
        })}
      </div>
    </>
  );
}

interface TopBarProps { onHamburger: () => void; }
function TopBarInner({ onHamburger }: TopBarProps) {
  const [status, setStatus] = useState<{ engine?: string; budget?: number; degraded?: boolean } | null>(null);
  const [time, setTime] = useState("");
  const [sseOk, setSseOk] = useState(true);

  useEffect(() => {
    const st = setInterval(() => setTime(new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })), 1000);
    let es: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      es = new EventSource("/api/athos-events");
      es.addEventListener("status", (e) => {
        try {
          const d = JSON.parse((e as MessageEvent).data);
          setStatus({ engine: d.engine, budget: d.budget, degraded: d.degraded });
          setSseOk(true);
        } catch {}
      });
      es.onerror = () => {
        if (cancelled) return;
        setSseOk(false);
        es?.close();
        retryTimer = setTimeout(connect, 10000);
      };
    };

    connect();
    return () => {
      cancelled = true;
      clearInterval(st);
      if (retryTimer) clearTimeout(retryTimer);
      es?.close();
    };
  }, []);

  const dot = !sseOk ? "var(--red)" : status ? (status.degraded ? "var(--yellow)" : "var(--green)") : "var(--border)";

  return (
    <header style={{
      height: "var(--topbar-h)", background: "var(--surface)", borderBottom: "1px solid var(--border)",
      display: "flex", alignItems: "center", padding: "0 16px", gap: 14, fontSize: 12, color: "var(--muted)", flexShrink: 0,
    }}>
      <button className="ds-hamburger" onClick={onHamburger} aria-label="Menu">☰</button>
      <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text)", fontWeight: 700, letterSpacing: 1, fontSize: 12 }}>
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: dot, boxShadow: `0 0 5px ${dot}`, display: "inline-block" }} />
        ATHOS
      </span>
      <span style={{ color: "var(--border)" }}>|</span>
      <span style={{ display: "flex", gap: 14, alignItems: "center", flex: 1, minWidth: 0, overflow: "hidden" }}>
        {status?.engine && (
          <span style={{ whiteSpace: "nowrap" }}>
            <span style={{ color: "var(--muted)" }}>Moteur </span>
            <span style={{ color: "var(--accent)", fontWeight: 600 }}>{status.engine}</span>
          </span>
        )}
        {status?.budget !== undefined && (
          <span style={{ whiteSpace: "nowrap" }} className="hide-mobile">
            <span style={{ color: "var(--muted)" }}>Budget </span>
            <span style={{ color: "var(--text)" }}>{status.budget.toFixed(3)}€</span>
          </span>
        )}
      </span>
      {time && <span style={{ fontSize: 10, color: "var(--border)", whiteSpace: "nowrap", marginLeft: "auto" }}>{time}</span>}
    </header>
  );
}

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const close = useCallback(() => setSidebarOpen(false), []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [close]);

  return (
    <div className="ds-root">
      <TopBarInner onHamburger={() => setSidebarOpen((v) => !v)} />
      <div className="ds-body">
        <div className={`ds-backdrop${sidebarOpen ? " open" : ""}`} onClick={close} />
        <nav className={`ds-sidebar${sidebarOpen ? " open" : ""}`}>
          <SidebarContent onNav={close} />
        </nav>
        <main className="ds-main">{children}</main>
      </div>
    </div>
  );
}
