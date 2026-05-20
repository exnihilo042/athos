import { MockBanner, SectionLabel, Badge, StatCard, PageHeader, InsetNotice } from "@/components/ui";

// ── Mock data — clearly identified ────────────────────────────────────────────
// Source future attendue : Shopify Admin API (orders) ou outil CRM/facturation.
// Toutes les constantes MOCK_ sont à remplacer par de vraies données.

const PIPELINE_STAGES = ["Devis", "Acompte", "En cours", "Livraison", "Facturé"];

type OrderStatus = "devis" | "acompte" | "en-cours" | "livraison" | "facture" | "annule";

interface MockOrder {
  id: string;
  client: string;
  project: string;
  type: string;
  amount: number;
  status: OrderStatus;
  stage: number;
  created: string;
  updated: string;
  notes?: string;
}

const MOCK_ORDERS: MockOrder[] = [
  {
    id: "CMD-2026-001",
    client: "Rouge Pivoine",
    project: "Thème Shopify sur mesure",
    type: "Développement Shopify",
    amount: 2800,
    status: "en-cours",
    stage: 2,
    created: "2026-04-25",
    updated: "2026-05-10",
    notes: "Design approuvé. Développement en cours.",
  },
  {
    id: "CMD-2026-002",
    client: "Olivia",
    project: "Theme Shopify olivia-16-5-3",
    type: "Développement Shopify",
    amount: 1600,
    status: "livraison",
    stage: 3,
    created: "2026-04-10",
    updated: "2026-05-15",
    notes: "À pousser sur GitHub. Validation client en attente.",
  },
  {
    id: "CMD-2026-003",
    client: "Placerr",
    project: "MVP SaaS — design variant",
    type: "Développement SaaS",
    amount: 400,
    status: "devis",
    stage: 0,
    created: "2026-05-15",
    updated: "2026-05-15",
    notes: "En attente choix variante design par Clément.",
  },
  {
    id: "CMD-2026-004",
    client: "MeetMe",
    project: "UI/UX responsive",
    type: "Design & Développement",
    amount: 1200,
    status: "acompte",
    stage: 1,
    created: "2026-05-01",
    updated: "2026-05-05",
    notes: "Bloqué : .env Supabase keys manquantes.",
  },
];

// ── Visual config ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<OrderStatus, { color: string; label: string }> = {
  devis:     { color: "var(--border)", label: "Devis" },
  acompte:   { color: "var(--yellow)", label: "Acompte" },
  "en-cours": { color: "var(--blue)",  label: "En cours" },
  livraison: { color: "var(--accent)", label: "Livraison" },
  facture:   { color: "var(--green)",  label: "Facturé" },
  annule:    { color: "var(--red)",    label: "Annulé" },
};

function formatDate(s: string): string {
  try {
    return new Date(s).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "2-digit" });
  } catch {
    return s;
  }
}

// ── Pipeline indicator ────────────────────────────────────────────────────────

function Pipeline({ stage }: { stage: number }) {
  return (
    <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
      {PIPELINE_STAGES.map((label, i) => {
        const done = i < stage;
        const active = i === stage;
        const color = done ? "var(--green)" : active ? "var(--accent)" : "var(--surface-2)";
        return (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 2 }}>
            <div
              style={{
                width: active ? 24 : 14,
                height: 5,
                background: color,
                borderRadius: 3,
                transition: "all 0.2s",
              }}
              title={label}
            />
          </div>
        );
      })}
    </div>
  );
}

// ── Order card ────────────────────────────────────────────────────────────────

function OrderCard({ order }: { order: MockOrder }) {
  const sc = STATUS_CONFIG[order.status];

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
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
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", marginBottom: 2 }}>
            {order.client}
          </div>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>{order.project}</div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center", flexShrink: 0 }}>
          <span
            style={{
              fontSize: 10,
              padding: "2px 7px",
              borderRadius: 20,
              background: `color-mix(in srgb, ${sc.color} 14%, transparent)`,
              color: sc.color,
              border: `1px solid color-mix(in srgb, ${sc.color} 28%, transparent)`,
              fontWeight: 500,
            }}
          >
            {sc.label}
          </span>
        </div>
      </div>

      {/* Pipeline */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <Pipeline stage={order.stage} />
        <span style={{ fontSize: 10, color: "var(--muted)" }}>
          {PIPELINE_STAGES[order.stage]}
        </span>
      </div>

      {/* Meta */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 6,
        }}
      >
        <div style={{ display: "flex", gap: 12, fontSize: 11, color: "var(--muted)" }}>
          <span style={{ fontFamily: "monospace", fontSize: 10, color: "var(--border)" }}>
            {order.id}
          </span>
          <span>{order.type}</span>
          <span>{formatDate(order.created)}</span>
        </div>
        <span style={{ fontSize: 16, fontWeight: 700, color: "var(--text)" }}>
          {order.amount.toLocaleString("fr-FR")} €
        </span>
      </div>

      {/* Notes */}
      {order.notes && (
        <div
          style={{
            fontSize: 11,
            color: "var(--muted)",
            background: "var(--surface-2)",
            borderRadius: 4,
            padding: "5px 10px",
          }}
        >
          {order.notes}
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function CommandesPage() {
  const total = MOCK_ORDERS.reduce((s, o) => s + o.amount, 0);
  const active = MOCK_ORDERS.filter((o) => !["facture", "annule", "devis"].includes(o.status));
  const byStatus = Object.keys(STATUS_CONFIG).reduce<Record<string, MockOrder[]>>((acc, k) => {
    acc[k] = MOCK_ORDERS.filter((o) => o.status === k);
    return acc;
  }, {});

  const pipelineGroups: { status: OrderStatus; orders: MockOrder[] }[] = (
    Object.entries(STATUS_CONFIG) as [OrderStatus, { color: string; label: string }][]
  )
    .map(([status]) => ({ status, orders: byStatus[status] ?? [] }))
    .filter(({ orders }) => orders.length > 0);

  return (
    <div style={{ maxWidth: 1000 }}>
      <PageHeader
        title="Commandes"
        subtitle="Pipeline projets agence — Ex-Nihilo Agency"
      />

      <MockBanner message="Données de démonstration. Connecter Shopify Admin API ou outil CRM pour les vraies commandes." />

      <InsetNotice
        icon="◱"
        text="Endpoint /api/commandes non implémenté"
        detail="Interface TypeScript : CommandesPayload dans dashboard/lib/types.ts · Source : Shopify Admin API · Scope Codex P2"
        variant="muted"
      />

      {/* KPI */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Volume pipeline"
          value={`${total.toLocaleString("fr-FR")} €`}
          sub="MOCK · tous statuts"
          color="var(--text)"
          size="lg"
        />
        <StatCard
          label="En cours"
          value={active.length}
          sub="MOCK · projets actifs"
          color="var(--blue)"
        />
        <StatCard
          label="Montant actif"
          value={`${active.reduce((s, o) => s + o.amount, 0).toLocaleString("fr-FR")} €`}
          sub="MOCK"
          color="var(--accent)"
        />
        <StatCard
          label="Commandes total"
          value={MOCK_ORDERS.length}
          sub="MOCK"
          color="var(--muted)"
        />
      </div>

      {/* Pipeline legend */}
      <div
        style={{
          display: "flex",
          gap: 4,
          alignItems: "center",
          marginBottom: 20,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "10px 14px",
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: 10, color: "var(--muted)", marginRight: 4 }}>Pipeline</span>
        {PIPELINE_STAGES.map((stage, i) => (
          <div key={stage} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            {i > 0 && <span style={{ color: "var(--border)", fontSize: 10 }}>→</span>}
            <span
              style={{
                fontSize: 10,
                padding: "2px 7px",
                borderRadius: 20,
                background: "var(--surface-2)",
                color: "var(--muted)",
                border: "1px solid var(--border)",
              }}
            >
              {stage}
            </span>
          </div>
        ))}
      </div>

      {/* Orders by status */}
      {pipelineGroups.map(({ status, orders }) => {
        const sc = STATUS_CONFIG[status];
        return (
          <div key={status} style={{ marginBottom: 20 }}>
            <SectionLabel count={orders.length}>
              <span style={{ color: sc.color }}>{sc.label}</span>
            </SectionLabel>
            <div className="grid-auto-2">
              {orders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>
          </div>
        );
      })}

      <div style={{ marginTop: 12, fontSize: 11, color: "var(--border)" }}>
        ⚠ Toutes les données sont MOCK — Source future : Shopify Admin API ou outil de facturation
      </div>
    </div>
  );
}
