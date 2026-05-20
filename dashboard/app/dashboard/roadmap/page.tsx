import { Card, Badge, SectionLabel } from "@/components/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

type RoadmapStatus = "done" | "active" | "blocked" | "pending" | "deferred";
type RoadmapOwner = "Claude" | "Codex" | "Clément" | "Externe";

interface RoadmapItem {
  id: string;
  title: string;
  status: RoadmapStatus;
  owner: RoadmapOwner;
  description: string;
  done?: string[];
  next?: string;
  blocker?: string;
  depends?: string[];
  priority: 0 | 1 | 2 | 3 | 4;
}

// ── Roadmap data — état réel au 2026-05-20 ───────────────────────────────────
// Source : athos_projects.mem + athos_kernel_plan.mem + session audit

const ROADMAP: RoadmapItem[] = [
  // ── P0 — Infrastructure fondamentale ────────────────────────────────────────
  {
    id: "P0-SERVER",
    title: "Serveur HUB ATHOS",
    status: "done",
    owner: "Codex",
    priority: 0,
    description: "HTTPServer ThreadingMixIn sur :7474, auth token, CORS strict, toutes les routes core.",
    done: [
      "ThreadingHTTPServer(ThreadingMixIn+HTTPServer) — daemon_threads = True",
      "Auth Bearer token sur toutes les routes",
      "CORS strict localhost",
      "Restart via scripts/restart_athos_hub.sh",
    ],
  },
  {
    id: "P0-SSE",
    title: "SSE live events",
    status: "done",
    owner: "Claude",
    priority: 0,
    description: "Flux temps réel kernel → dashboard. Proxy Next.js GET /api/athos-events → POST :7474/api/events.",
    done: [
      "Route POST /api/events dans voice/server.py",
      "Seed event status corrigé (router.status() au lieu de get_status() manquant)",
      "Proxy SSE Next.js /api/athos-events",
      "LiveFeed.tsx client avec reconnexion auto",
      "TopBar SSE remplace le polling 30s",
    ],
  },
  {
    id: "P0-DASHBOARD",
    title: "Dashboard Next.js",
    status: "done",
    owner: "Claude",
    priority: 0,
    description: "Dashboard cockpit ATHOS — 15 routes, responsive mobile/desktop, design system.",
    done: [
      "Hub, Room, Agents, Alertes, Projects, Settings, Finances, SEO, Roadmap, Commandes",
      "DashboardShell responsive (hamburger + drawer mobile)",
      "Composants UI partagés (/components/ui/index.tsx)",
      "TypeScript contracts complets (/lib/types.ts)",
    ],
  },
  {
    id: "P0-MEMORY",
    title: "Mémoire persistante",
    status: "done",
    owner: "Codex",
    priority: 0,
    description: "Format §-compressé. Fichiers canoniques. Stop hook Claude Code.",
    done: [
      "Tous les fichiers canoniques présents et valides",
      "memory.ok = true (vérifié /api/observability)",
      "/api/memory/note — endpoint pour Codex CLI",
    ],
  },

  // ── P1 — Stabilisation opérationnelle ────────────────────────────────────────
  {
    id: "P1-CODEX-RESPONDER",
    title: "Codex responder — retour quota",
    status: "blocked",
    owner: "Externe",
    priority: 1,
    description: "Responder chatgpt_plus (Codex CLI) bloqué par usage_limit ChatGPT Plus.",
    blocker: "Reset quota ChatGPT Plus — délai inconnu",
    next: "Attendre reset. Une fois disponible : vérifier room auto-respond avec les deux engines.",
    depends: [],
  },
  {
    id: "P1-SESSION-WRITER",
    title: "session_writer E2E Codex",
    status: "blocked",
    owner: "Codex",
    priority: 1,
    description: "write_session() jamais appelé par Codex CLI → mémoire session Codex non persistée.",
    blocker: "Nécessite Codex CLI actif. Impossible à tester sans.",
    next: "À P1 retour Codex : appeler POST /api/memory/note avant exit.",
    done: ["Endpoint /api/memory/note ajouté et fonctionnel (Claude 2026-05-20)"],
    depends: ["P1-CODEX-RESPONDER"],
  },
  {
    id: "P1-TASK-QUEUE-UI",
    title: "Task queue — contrôles UI",
    status: "pending",
    owner: "Codex",
    priority: 1,
    description: "Boutons pause/retry/cancel/resume dans la page Automations.",
    next: "Codex valide les endpoints de mutation dans /api/tasks, puis Claude implémente les boutons.",
    done: [
      "Interface TypeScript TaskCardProps, TaskQueueViewProps dans lib/types.ts",
      "Task queue backend existe (core/task_queue.py, 194 tests)",
    ],
    depends: ["P1-CODEX-RESPONDER"],
  },
  {
    id: "P1-REPORTS",
    title: "Rapports — endpoint /api/report",
    status: "pending",
    owner: "Codex",
    priority: 1,
    description: "Page Reports appelle /api/report { type: 'daily' }. Endpoint à valider et enrichir.",
    next: "Codex vérifie que l'endpoint retourne le schéma attendu : { brief, date, sections }.",
  },

  // ── P2 — Modules métier ────────────────────────────────────────────────────
  {
    id: "P2-FINANCES-REAL",
    title: "Finances — données réelles",
    status: "deferred",
    owner: "Clément",
    priority: 2,
    description: "Page Finances exist avec mock data. Besoin d'une source réelle.",
    next: "Clément choisit la source : Stripe API, Shopify Admin API, ou fichier.",
    done: ["Page /dashboard/finances créée avec MOCK data clairement marquée"],
    depends: [],
  },
  {
    id: "P2-SEO-REAL",
    title: "SEO Analytics — données réelles",
    status: "deferred",
    owner: "Codex",
    priority: 2,
    description: "Page SEO existe avec mock. Intégration Google Search Console API nécessaire.",
    next: "Codex implémente /api/seo avec GSC OAuth. Claude connecte au dashboard.",
    done: ["Page /dashboard/seo créée avec MOCK data"],
    depends: [],
  },
  {
    id: "P2-AUTONOMOUS-LOOP",
    title: "Boucle autonome — contrôles UI",
    status: "pending",
    owner: "Codex",
    priority: 2,
    description: "Boutons Start/Stop pour autonomous_loop. Feedback SSE temps réel.",
    depends: ["P1-TASK-QUEUE-UI"],
  },

  // ── P3 — Vision produit ────────────────────────────────────────────────────
  {
    id: "P3-COMMANDES",
    title: "Commandes — données réelles",
    status: "deferred",
    owner: "Clément",
    priority: 3,
    description: "Page Commandes exist avec mock data. Besoin source : Shopify Admin API ou outil CRM.",
    done: ["Page /dashboard/commandes créée avec MOCK data"],
  },
  {
    id: "P3-CRM",
    title: "CRM / Clients",
    status: "deferred",
    owner: "Clément",
    priority: 3,
    description: "Module gestion clients, contacts, prospects. Pas de source définie.",
    next: "Définir l'outil source avant de construire le module.",
  },
  {
    id: "P3-PERFORMANCE",
    title: "Performance — monitoring",
    status: "deferred",
    owner: "Codex",
    priority: 3,
    description: "Uptime, Lighthouse, temps de réponse API. Sources : Lighthouse CLI, ping checks.",
  },

  // ── P4 — Vision long terme ─────────────────────────────────────────────────
  {
    id: "P4-VOICE-IOS",
    title: "PWA Voix — iOS native feel",
    status: "pending",
    owner: "Claude",
    priority: 4,
    description: "Améliorer l'expérience voix iPhone (orb, STT, TTS, seamless loop).",
  },
  {
    id: "P4-AGENCY-OPS",
    title: "Opérations agence autonomes",
    status: "deferred",
    owner: "Codex",
    priority: 4,
    description: "ATHOS gère seul la prospection, le devis, le suivi client. Objectif 50K€/mois autonome.",
    depends: ["P2-FINANCES-REAL", "P3-CRM", "P3-COMMANDES"],
  },
];

// ── Visual config ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<RoadmapStatus, { color: string; label: string; icon: string }> = {
  done:     { color: "var(--green)",  label: "Terminé",  icon: "✓" },
  active:   { color: "var(--accent)", label: "En cours", icon: "◉" },
  blocked:  { color: "var(--red)",    label: "Bloqué",   icon: "⚠" },
  pending:  { color: "var(--blue)",   label: "Planifié", icon: "◱" },
  deferred: { color: "var(--border)", label: "Différé",  icon: "◫" },
};

const OWNER_BADGE: Record<RoadmapOwner, { variant: "accent" | "green" | "blue" | "muted" }> = {
  Claude:   { variant: "accent" },
  Codex:    { variant: "green" },
  Clément:  { variant: "blue" },
  Externe:  { variant: "muted" },
};

const PRIORITY_LABELS = ["P0 — Infrastructure", "P1 — Stabilisation", "P2 — Modules métier", "P3 — Vision produit", "P4 — Long terme"];

// ── Components ────────────────────────────────────────────────────────────────

function RoadmapCard({ item }: { item: RoadmapItem }) {
  const sc = STATUS_CONFIG[item.status];
  const ow = OWNER_BADGE[item.owner];

  return (
    <div
      style={{
        background: "var(--surface)",
        border: `1px solid ${item.status === "blocked" ? "rgba(255,69,58,0.25)" : "var(--border)"}`,
        borderLeft: `3px solid ${sc.color}`,
        borderRadius: 8,
        padding: "12px 14px",
        opacity: item.status === "deferred" ? 0.7 : 1,
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
        <span style={{ color: sc.color, fontSize: 11, marginTop: 2, flexShrink: 0 }}>{sc.icon}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", flex: 1 }}>{item.title}</span>
        <Badge label={sc.label} variant={item.status === "done" ? "green" : item.status === "blocked" ? "red" : item.status === "active" ? "accent" : item.status === "pending" ? "blue" : "border"} />
        <Badge label={item.owner} variant={ow.variant} />
      </div>

      <p style={{ fontSize: 12, color: "var(--muted)", margin: "0 0 8px 19px", lineHeight: 1.5 }}>
        {item.description}
      </p>

      {item.blocker && (
        <div style={{ marginLeft: 19, marginBottom: 8, fontSize: 11, color: "var(--red)", display: "flex", gap: 5 }}>
          <span>⛔</span>
          <span>{item.blocker}</span>
        </div>
      )}

      {item.next && item.status !== "done" && (
        <div style={{ marginLeft: 19, marginBottom: 6, fontSize: 11, color: "var(--accent)", display: "flex", gap: 5 }}>
          <span>→</span>
          <span>{item.next}</span>
        </div>
      )}

      {(item.done ?? []).length > 0 && (
        <div style={{ marginLeft: 19, marginTop: 4 }}>
          {(item.done!).map((d, i) => (
            <div key={i} style={{ fontSize: 11, color: "var(--muted)", display: "flex", gap: 5, marginBottom: 2 }}>
              <span style={{ color: "var(--green)" }}>✓</span>
              <span>{d}</span>
            </div>
          ))}
        </div>
      )}

      {(item.depends ?? []).length > 0 && (
        <div style={{ marginLeft: 19, marginTop: 6, fontSize: 10, color: "var(--border)" }}>
          Dépend de : {item.depends!.join(", ")}
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function RoadmapPage() {
  const done = ROADMAP.filter((i) => i.status === "done").length;
  const active = ROADMAP.filter((i) => i.status === "active" || i.status === "pending").length;
  const blocked = ROADMAP.filter((i) => i.status === "blocked").length;

  const byPriority = [0, 1, 2, 3, 4].map((p) => ({
    priority: p,
    label: PRIORITY_LABELS[p],
    items: ROADMAP.filter((i) => i.priority === p),
  }));

  return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Roadmap ATHOS</h1>
        <p style={{ color: "var(--muted)", fontSize: 13, margin: "0 0 16px" }}>
          État réel au 2026-05-20 · Source : athos_kernel_plan.mem + audit sessions
        </p>

        {/* Summary stats */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {[
            { label: "Terminés", value: done, color: "var(--green)" },
            { label: "En cours / planifiés", value: active, color: "var(--blue)" },
            { label: "Bloqués", value: blocked, color: "var(--red)" },
            { label: "Total", value: ROADMAP.length, color: "var(--muted)" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
              <span style={{ fontWeight: 700, color, fontSize: 16 }}>{value}</span>
              <span style={{ color: "var(--muted)" }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 24 }}>
        {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: cfg.color }}>
            <span>{cfg.icon}</span>
            <span>{cfg.label}</span>
          </div>
        ))}
        <span style={{ color: "var(--border)", fontSize: 11 }}>·</span>
        {(["Claude", "Codex", "Clément", "Externe"] as RoadmapOwner[]).map((o) => (
          <Badge key={o} label={o} variant={OWNER_BADGE[o].variant} />
        ))}
      </div>

      {/* Roadmap by priority */}
      {byPriority.map(({ label, items }) => (
        <div key={label} style={{ marginBottom: 28 }}>
          <SectionLabel count={items.length}>{label}</SectionLabel>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {items.map((item) => (
              <RoadmapCard key={item.id} item={item} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
