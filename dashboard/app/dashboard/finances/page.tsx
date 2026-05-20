import { athosPost } from "@/lib/athos";
import { Card, StatCard, MockBanner, BarChart, DataRow, SectionLabel } from "@/components/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

interface StatusPayload {
  budget?: number;
  spend_policy?: { mode?: string };
}

// ── Mock data — clearly identified ────────────────────────────────────────────
// All MOCK_ constants must be replaced by real data sources when available.
// Candidates: Stripe API, Shopify Admin API, Dolibarr, Google Sheets via /api/finances.

const MOCK_CA_MONTH = 4800;
const MOCK_VENTES_NETTES = 4200;
const MOCK_COMMANDES = 3;
const MOCK_MARGE_PCT = 72;
const MOCK_COMMISSION_RATE = 0.15;
const MOCK_REVENUE_MONTHLY = [
  { label: "Nov", value: 1200 },
  { label: "Déc", value: 900 },
  { label: "Jan", value: 2400 },
  { label: "Fév", value: 1800 },
  { label: "Mar", value: 3200 },
  { label: "Avr", value: 4800 },
];
const MOCK_PROJECTS_REVENUE = [
  { name: "Rouge Pivoine", type: "Shopify theme", amount: 2800, status: "facturé" },
  { name: "Olivia", type: "Shopify theme", amount: 1600, status: "en cours" },
  { name: "Placerr (MVP)", type: "SaaS dev", amount: 400, status: "devis" },
];

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function FinancesPage() {
  let status: StatusPayload = {};
  try {
    status = await athosPost<StatusPayload>("/api/status");
  } catch {}

  const athosBudget = status.budget ?? 0;
  const spendMode = status.spend_policy?.mode ?? "zero_paid_api";

  const commissions = MOCK_CA_MONTH * MOCK_COMMISSION_RATE;
  const resultatNet = MOCK_VENTES_NETTES - commissions;

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>Finances</h1>
        <p style={{ color: "var(--muted)", fontSize: 13, margin: 0 }}>
          Vue financière agence — Ex-Nihilo Agency
        </p>
      </div>

      <MockBanner message="Chiffres métier fictifs. Seul le budget ATHOS est réel (source : /api/status). Brancher Stripe ou Shopify Admin API pour les vraies valeurs." />

      {/* ── KPI primaires ── */}
      <div className="grid-auto-4" style={{ marginBottom: 16 }}>
        <StatCard
          label="CA du mois"
          value={`${MOCK_CA_MONTH.toLocaleString("fr-FR")} €`}
          sub="MOCK · mai 2026"
          color="var(--text)"
          size="lg"
        />
        <StatCard
          label="Ventes nettes"
          value={`${MOCK_VENTES_NETTES.toLocaleString("fr-FR")} €`}
          sub="MOCK · après remises"
          color="var(--green)"
        />
        <StatCard
          label="Commandes"
          value={MOCK_COMMANDES}
          sub="MOCK · projets actifs"
          color="var(--blue)"
        />
        <StatCard
          label="Marge brute"
          value={`${MOCK_MARGE_PCT}%`}
          sub="MOCK · services uniquement"
          color={MOCK_MARGE_PCT >= 70 ? "var(--green)" : "var(--yellow)"}
        />
      </div>

      {/* ── Résultat ATHOS (réel) + commission ── */}
      <div className="grid-auto-2" style={{ marginBottom: 16 }}>
        <Card title="Résultat ATHOS — réel">
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)", marginBottom: 4 }}>
              {athosBudget.toFixed(4)} €
            </div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>
              Dépenses API ATHOS cumulées · source réelle via /api/status
            </div>
          </div>
          <DataRow label="Mode dépense" value={spendMode} mono />
          <DataRow label="API payante" value={spendMode === "zero_paid_api" ? "désactivée" : "active"} color={spendMode === "zero_paid_api" ? "var(--green)" : "var(--yellow)"} />
        </Card>

        <Card title="Commissions & résultat net — MOCK">
          <DataRow label="CA brut" value={`${MOCK_CA_MONTH.toLocaleString("fr-FR")} €`} />
          <DataRow label="Taux commission" value={`${(MOCK_COMMISSION_RATE * 100).toFixed(0)}%`} />
          <DataRow
            label="Commissions versées"
            value={`${commissions.toLocaleString("fr-FR")} €`}
            color="var(--yellow)"
          />
          <DataRow
            label="Résultat net estimé"
            value={`${resultatNet.toLocaleString("fr-FR")} €`}
            color="var(--green)"
          />
        </Card>
      </div>

      {/* ── Évolution mensuelle ── */}
      <Card title="Revenus mensuels — MOCK" noPad>
        <div style={{ padding: "16px 16px 12px" }}>
          <BarChart data={MOCK_REVENUE_MONTHLY} height={130} color="var(--accent)" />
        </div>
        <div style={{ padding: "0 16px 12px", fontSize: 11, color: "var(--border)" }}>
          Données mock — Connecter Stripe ou Shopify Admin API pour l'historique réel
        </div>
      </Card>

      {/* ── Projets en cours ── */}
      <div style={{ marginTop: 16 }}>
        <SectionLabel count={MOCK_PROJECTS_REVENUE.length}>Projets — répartition CA</SectionLabel>
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          {MOCK_PROJECTS_REVENUE.map((proj, i) => {
            const pct = Math.round((proj.amount / MOCK_CA_MONTH) * 100);
            const statusColor =
              proj.status === "facturé" ? "var(--green)" :
              proj.status === "en cours" ? "var(--blue)" :
              "var(--border)";
            return (
              <div
                key={proj.name}
                style={{
                  padding: "12px 16px",
                  borderBottom: i < MOCK_PROJECTS_REVENUE.length - 1 ? "1px solid var(--border)" : "none",
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  flexWrap: "wrap",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{proj.name}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)" }}>{proj.type}</div>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    fontSize: 12,
                  }}
                >
                  <div
                    style={{
                      width: 80,
                      height: 4,
                      background: "var(--surface-2)",
                      borderRadius: 2,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${pct}%`,
                        background: "var(--accent)",
                        borderRadius: 2,
                      }}
                    />
                  </div>
                  <span style={{ color: "var(--muted)", minWidth: 28, textAlign: "right" }}>{pct}%</span>
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", minWidth: 80, textAlign: "right" }}>
                  {proj.amount.toLocaleString("fr-FR")} €
                </span>
                <span
                  style={{
                    fontSize: 10,
                    padding: "2px 7px",
                    borderRadius: 20,
                    background: `color-mix(in srgb, ${statusColor} 14%, transparent)`,
                    color: statusColor,
                    border: `1px solid color-mix(in srgb, ${statusColor} 28%, transparent)`,
                    fontWeight: 500,
                  }}
                >
                  {proj.status}
                </span>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--border)" }}>
          ⚠ Données MOCK — intégrer Shopify Admin API ou outil comptable pour les vraies commandes
        </div>
      </div>
    </div>
  );
}
