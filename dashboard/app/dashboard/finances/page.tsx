import { athosPost } from "@/lib/athos";
import { Card, StatCard, MockBanner, BarChart, DataRow, SectionLabel, PageHeader, InsetNotice, Badge } from "@/components/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

interface StatusPayload {
  budget?: number;
  spend_policy?: { mode?: string; paid_api_enabled?: boolean };
}

// ── Mock data — isolé, remplaçable par /api/finances ─────────────────────────
// Toutes les constantes MOCK.* doivent être remplacées par des données réelles.
// Endpoint cible : POST /api/finances → FinancesSummary (voir dashboard/lib/types.ts)
// Sources candidates : Stripe API, Shopify Admin API, Dolibarr.

type ProjectStatus = "facturé" | "en cours" | "devis" | "annulé";
interface MockProject { name: string; type: string; amount: number; status: ProjectStatus }

const MOCK: {
  period: string; ca: number; ventes_nettes: number; commandes: number;
  marge_pct: number; commission_rate: number;
  revenue_monthly: { label: string; value: number }[];
  projects: MockProject[];
  projection_q3: number;
} = {
  period: "mai 2026",
  ca: 4800,
  ventes_nettes: 4200,
  commandes: 3,
  marge_pct: 72,
  commission_rate: 0.15,
  revenue_monthly: [
    { label: "Nov", value: 1200 },
    { label: "Déc", value: 900 },
    { label: "Jan", value: 2400 },
    { label: "Fév", value: 1800 },
    { label: "Mar", value: 3200 },
    { label: "Avr", value: 4800 },
  ],
  projects: [
    { name: "Rouge Pivoine", type: "Shopify theme", amount: 2800, status: "facturé" },
    { name: "Olivia",        type: "Shopify theme", amount: 1600, status: "en cours" },
    { name: "Placerr (MVP)", type: "SaaS dev",      amount: 400,  status: "devis" },
  ],
  projection_q3: 14000,
};

const STATUS_COLOR: Record<string, string> = {
  "facturé":  "var(--green)",
  "en cours": "var(--blue)",
  "devis":    "var(--border)",
  "annulé":   "var(--red)",
};

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function FinancesPage() {
  let status: StatusPayload = {};
  try {
    status = await athosPost<StatusPayload>("/api/status");
  } catch {}

  const athosBudget = status.budget ?? 0;
  const spendMode = status.spend_policy?.mode ?? "zero_paid_api";
  const paidApiEnabled = status.spend_policy?.paid_api_enabled ?? false;

  const commissions = MOCK.ca * MOCK.commission_rate;
  const resultatNet = MOCK.ventes_nettes - commissions;
  const backlog = MOCK.projects.filter((p) => p.status !== "facturé" && p.status !== "annulé");
  const backlogTotal = backlog.reduce((s, p) => s + p.amount, 0);

  return (
    <div style={{ maxWidth: 1100 }}>
      <PageHeader
        title="Finances"
        subtitle={`Vue financière agence — Ex-Nihilo Agency · ${MOCK.period}`}
      />

      <MockBanner message="Chiffres métier fictifs. Seul le budget ATHOS est réel (source : /api/status). Brancher Stripe ou Shopify Admin API pour les vraies valeurs." />

      <InsetNotice
        icon="◱"
        text="Endpoint /api/finances non implémenté"
        detail="Interface TypeScript : FinancesSummary dans dashboard/lib/types.ts · Scope Codex P2"
        variant="muted"
      />

      {/* ── KPI primaires ── */}
      <div className="grid-auto-4" style={{ marginBottom: 16 }}>
        <StatCard
          label="CA du mois"
          value={`${MOCK.ca.toLocaleString("fr-FR")} €`}
          sub={`MOCK · ${MOCK.period}`}
          color="var(--text)"
          size="lg"
        />
        <StatCard
          label="Ventes nettes"
          value={`${MOCK.ventes_nettes.toLocaleString("fr-FR")} €`}
          sub="MOCK · après remises"
          color="var(--green)"
        />
        <StatCard
          label="Marge brute"
          value={`${MOCK.marge_pct}%`}
          sub="MOCK · services uniquement"
          color={MOCK.marge_pct >= 70 ? "var(--green)" : "var(--yellow)"}
        />
        <StatCard
          label="Backlog facturable"
          value={`${backlogTotal.toLocaleString("fr-FR")} €`}
          sub={`${backlog.length} projet(s) en attente`}
          color="var(--accent)"
        />
      </div>

      {/* ── Budget ATHOS (réel) + résultat net ── */}
      <div className="grid-auto-2" style={{ marginBottom: 16 }}>
        <Card title="Budget ATHOS — RÉEL">
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 26, fontWeight: 700, color: "var(--accent)", marginBottom: 4 }}>
              {athosBudget.toFixed(4)} €
            </div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>
              Dépenses API ATHOS cumulées · source réelle /api/status
            </div>
          </div>
          <DataRow label="Mode dépense" value={spendMode} mono />
          <DataRow label="API payante" value={paidApiEnabled ? "active" : "désactivée"} color={paidApiEnabled ? "var(--yellow)" : "var(--green)"} />
          <DataRow
            label="Coût/session"
            value={athosBudget > 0 ? `${athosBudget.toFixed(6)} €` : "gratuit (zéro spend)"}
            color="var(--muted)"
          />
        </Card>

        <Card title="Résultat net estimé — MOCK">
          <DataRow label="CA brut"             value={`${MOCK.ca.toLocaleString("fr-FR")} €`} />
          <DataRow label="Ventes nettes"       value={`${MOCK.ventes_nettes.toLocaleString("fr-FR")} €`} />
          <DataRow
            label={`Commissions (${(MOCK.commission_rate * 100).toFixed(0)}%)`}
            value={`− ${commissions.toLocaleString("fr-FR")} €`}
            color="var(--yellow)"
          />
          <DataRow label="Résultat net"        value={`${resultatNet.toLocaleString("fr-FR")} €`} color="var(--green)" />
          <DataRow label="Projection Q3 2026"  value={`${MOCK.projection_q3.toLocaleString("fr-FR")} €`} color="var(--muted)" />
        </Card>
      </div>

      {/* ── Revenus mensuels ── */}
      <Card title="Revenus mensuels — MOCK" noPad>
        <div style={{ padding: "16px 16px 8px" }}>
          <BarChart data={MOCK.revenue_monthly} height={130} color="var(--accent)" />
        </div>
        <div style={{ padding: "0 16px 12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "var(--border)" }}>
            Connecter Stripe ou Shopify Admin API pour l'historique réel
          </span>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>
            Moy. : {Math.round(MOCK.revenue_monthly.reduce((s, d) => s + d.value, 0) / MOCK.revenue_monthly.length).toLocaleString("fr-FR")} €/mois
          </span>
        </div>
      </Card>

      {/* ── Projets — répartition CA ── */}
      <div style={{ marginTop: 16 }}>
        <SectionLabel count={MOCK.projects.length}>Projets — répartition CA · MOCK</SectionLabel>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          {MOCK.projects.map((proj, i) => {
            const pct = Math.round((proj.amount / MOCK.ca) * 100);
            const color = STATUS_COLOR[proj.status] ?? "var(--border)";
            return (
              <div
                key={proj.name}
                style={{
                  padding: "12px 16px",
                  borderBottom: i < MOCK.projects.length - 1 ? "1px solid var(--border)" : "none",
                  borderLeft: `3px solid ${color}`,
                  display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{proj.name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>{proj.type}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 80, height: 4, background: "var(--surface-2)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: "var(--accent)", borderRadius: 2 }} />
                  </div>
                  <span style={{ color: "var(--muted)", fontSize: 11, minWidth: 28, textAlign: "right" }}>{pct}%</span>
                </div>
                <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text)", minWidth: 80, textAlign: "right" }}>
                  {proj.amount.toLocaleString("fr-FR")} €
                </span>
                <Badge
                  label={proj.status}
                  variant={proj.status === "facturé" ? "green" : proj.status === "en cours" ? "blue" : proj.status === "annulé" ? "red" : "border"}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
