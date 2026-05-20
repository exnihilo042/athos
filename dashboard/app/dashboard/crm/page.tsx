import { MockBanner, SectionLabel, StatCard, Badge, PageHeader } from "@/components/ui";

// ── Mock data — clearly identified ────────────────────────────────────────────
// Source future : outil CRM (Notion, HubSpot, Dolibarr, fichier JSON)
// Endpoint à créer : /api/crm (scope Codex)
// Ces données reflètent l'état réel des projets au 2026-05-20 (valeurs approximatives)

type ClientStatus = "active" | "prospect" | "blocked" | "done" | "paused";
type AttentionLevel = "high" | "medium" | "low";

interface MockClient {
  id: string;
  name: string;
  status: ClientStatus;
  type: string;
  project: string;
  amount: number;
  attention: AttentionLevel;
  lastActivity: string;
  nextAction: string;
  blocker?: string;
  tags: string[];
}

const MOCK_CLIENTS: MockClient[] = [
  {
    id: "c-001",
    name: "Rouge Pivoine",
    status: "active",
    type: "Boutique Shopify",
    project: "Thème Shopify sur mesure",
    amount: 2800,
    attention: "high",
    lastActivity: "2026-05-10",
    nextAction: "Livraison thème + formation admin",
    tags: ["Shopify", "E-commerce"],
  },
  {
    id: "c-002",
    name: "Olivia",
    status: "active",
    type: "Boutique Shopify",
    project: "Theme olivia-16-5-3 — à valider",
    amount: 1600,
    attention: "medium",
    lastActivity: "2026-05-15",
    nextAction: "Push GitHub + validation client",
    tags: ["Shopify", "Live"],
  },
  {
    id: "c-003",
    name: "Placerr",
    status: "prospect",
    type: "SaaS",
    project: "MVP SaaS — choix variante design",
    amount: 400,
    attention: "low",
    lastActivity: "2026-05-15",
    nextAction: "Attendre choix variante design",
    tags: ["SaaS", "MVP"],
  },
  {
    id: "c-004",
    name: "MeetMe",
    status: "blocked",
    type: "App Web",
    project: "UI/UX responsive — acompte reçu",
    amount: 1200,
    attention: "high",
    lastActivity: "2026-05-05",
    nextAction: "Débloquer les clés Supabase .env",
    blocker: "Clés Supabase .env manquantes côté client",
    tags: ["UI/UX", "React"],
  },
];

// ── Visual config ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<ClientStatus, { color: string; label: string }> = {
  active:   { color: "var(--green)",  label: "Actif" },
  prospect: { color: "var(--blue)",   label: "Prospect" },
  blocked:  { color: "var(--red)",    label: "Bloqué" },
  done:     { color: "var(--muted)",  label: "Terminé" },
  paused:   { color: "var(--border)", label: "En pause" },
};

const ATTENTION_CONFIG: Record<AttentionLevel, { color: string; label: string; variant: "red" | "yellow" | "muted" }> = {
  high:   { color: "var(--red)",    label: "Urgent",   variant: "red" },
  medium: { color: "var(--yellow)", label: "À suivre", variant: "yellow" },
  low:    { color: "var(--muted)",  label: "OK",       variant: "muted" },
};

const STATUS_BADGE_VARIANT: Record<ClientStatus, "green" | "blue" | "red" | "muted" | "border"> = {
  active:   "green",
  prospect: "blue",
  blocked:  "red",
  done:     "muted",
  paused:   "border",
};

function formatDate(s: string): string {
  try {
    return new Date(s).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "2-digit" });
  } catch { return s; }
}

// ── Client card ───────────────────────────────────────────────────────────────

function ClientCard({ client }: { client: MockClient }) {
  const sc = STATUS_CONFIG[client.status];
  const ac = ATTENTION_CONFIG[client.attention];

  return (
    <div
      style={{
        background: "var(--surface)",
        border: `1px solid ${client.status === "blocked" ? "rgba(255,69,58,0.25)" : "var(--border)"}`,
        borderLeft: `3px solid ${sc.color}`,
        borderRadius: 8,
        padding: "14px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 8, flexWrap: "wrap" }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", marginBottom: 2 }}>
            {client.name}
          </div>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>{client.type}</div>
        </div>
        <div style={{ display: "flex", gap: 5, alignItems: "center", flexShrink: 0 }}>
          <Badge label={ac.label} variant={ac.variant} dot />
          <Badge label={sc.label} variant={STATUS_BADGE_VARIANT[client.status]} />
        </div>
      </div>

      {/* Project */}
      <div style={{ fontSize: 12, color: "var(--text)" }}>
        <span style={{ color: "var(--border)", marginRight: 6 }}>◱</span>
        {client.project}
      </div>

      {/* Blocker */}
      {client.blocker && (
        <div
          style={{
            fontSize: 11,
            color: "var(--red)",
            background: "rgba(255,69,58,0.08)",
            borderRadius: 4,
            padding: "5px 10px",
            display: "flex",
            gap: 6,
          }}
        >
          <span>⛔</span>
          <span>{client.blocker}</span>
        </div>
      )}

      {/* Next action */}
      <div style={{ fontSize: 11, display: "flex", gap: 6, color: "var(--accent)" }}>
        <span>→</span>
        <span>{client.nextAction}</span>
      </div>

      {/* Tags + meta */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 6,
          paddingTop: 4,
          borderTop: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {client.tags.map((tag) => (
            <span
              key={tag}
              style={{
                fontSize: 10,
                padding: "1px 7px",
                borderRadius: 20,
                background: "var(--surface-2)",
                color: "var(--muted)",
                border: "1px solid var(--border)",
              }}
            >
              {tag}
            </span>
          ))}
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "var(--border)" }}>{formatDate(client.lastActivity)}</span>
          <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text)" }}>
            {client.amount.toLocaleString("fr-FR")} €
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function CrmPage() {
  const total = MOCK_CLIENTS.reduce((s, c) => s + c.amount, 0);
  const active = MOCK_CLIENTS.filter((c) => c.status === "active");
  const urgent = MOCK_CLIENTS.filter((c) => c.attention === "high");
  const blocked = MOCK_CLIENTS.filter((c) => c.status === "blocked");

  const byStatus: Record<ClientStatus, MockClient[]> = {
    active:   [],
    blocked:  [],
    prospect: [],
    done:     [],
    paused:   [],
  };
  for (const c of MOCK_CLIENTS) byStatus[c.status].push(c);

  const groups: { status: ClientStatus; clients: MockClient[] }[] = (
    Object.entries(STATUS_CONFIG) as [ClientStatus, { color: string; label: string }][]
  )
    .map(([status]) => ({ status, clients: byStatus[status] }))
    .filter(({ clients }) => clients.length > 0);

  return (
    <div style={{ maxWidth: 1000 }}>
      <PageHeader
        title="CRM / Clients"
        subtitle="Gestion relation client — Ex-Nihilo Agency"
      />

      <MockBanner message="Données de démonstration. Connecter un outil CRM (Notion, HubSpot, fichier JSON) pour les vraies fiches client." />

      {/* KPI */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Pipeline total"
          value={`${total.toLocaleString("fr-FR")} €`}
          sub="MOCK · tous clients"
          color="var(--text)"
          size="lg"
        />
        <StatCard
          label="Clients actifs"
          value={active.length}
          sub="MOCK · projets en cours"
          color="var(--green)"
        />
        <StatCard
          label="Attention urgente"
          value={urgent.length}
          sub="MOCK · à traiter"
          color={urgent.length > 0 ? "var(--red)" : "var(--green)"}
        />
        <StatCard
          label="Bloqués"
          value={blocked.length}
          sub="MOCK · nécessitent action"
          color={blocked.length > 0 ? "var(--yellow)" : "var(--green)"}
        />
      </div>

      {/* Clients par statut */}
      {groups.map(({ status, clients }) => {
        const sc = STATUS_CONFIG[status];
        return (
          <div key={status} style={{ marginBottom: 20 }}>
            <SectionLabel count={clients.length}>
              <span style={{ color: sc.color }}>{sc.label}</span>
            </SectionLabel>
            <div className="grid-auto-2">
              {clients.map((client) => (
                <ClientCard key={client.id} client={client} />
              ))}
            </div>
          </div>
        );
      })}

      <div style={{ marginTop: 12, fontSize: 11, color: "var(--border)" }}>
        ⚠ Toutes les données sont MOCK — Source future : outil CRM ou endpoint /api/crm (Codex)
      </div>
    </div>
  );
}
