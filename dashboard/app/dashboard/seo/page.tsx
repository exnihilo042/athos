import { Card, StatCard, MockBanner, Gauge, SectionLabel, Badge, PageHeader, InsetNotice } from "@/components/ui";

// ── Mock data — clearly identified ────────────────────────────────────────────
// All data below is MOCK. Sources à brancher :
// - Google Search Console API (positions, clics, impressions)
// - Google PageSpeed Insights API (CWV)
// - Screaming Frog / Ahrefs API (erreurs crawl)
// - GA4 ou Plausible Analytics (trafic)

const MOCK_SITES = [
  {
    name: "ex-nihilo.agency",
    score: 74,
    traffic: 1240,
    positions_top10: 12,
    errors: 3,
    status: "warn",
  },
  {
    name: "rouge-pivoine.fr",
    score: 61,
    traffic: 3800,
    positions_top10: 8,
    errors: 7,
    status: "warn",
  },
  {
    name: "placerr.app",
    score: 0,
    traffic: 0,
    positions_top10: 0,
    errors: 0,
    status: "nodata",
  },
];

const MOCK_CWV = {
  LCP: { value: "2.4s", score: 78, target: "< 2.5s", ok: true },
  FID: { value: "18ms", score: 95, target: "< 100ms", ok: true },
  CLS: { value: "0.12", score: 52, target: "< 0.1", ok: false },
  TTFB: { value: "620ms", score: 65, target: "< 600ms", ok: false },
};

const MOCK_POSITIONS = [
  { keyword: "agence shopify france", position: 7, clicks: 42, impressions: 580, trend: "up" },
  { keyword: "développeur shopify freelance", position: 12, clicks: 18, impressions: 290, trend: "stable" },
  { keyword: "theme shopify sur mesure", position: 9, clicks: 31, impressions: 410, trend: "up" },
  { keyword: "boutique rouge pivoine", position: 3, clicks: 95, impressions: 1200, trend: "up" },
  { keyword: "fleurs pivoine en ligne", position: 15, clicks: 8, impressions: 180, trend: "down" },
];

const MOCK_ERRORS = [
  { type: "4xx", count: 7, severity: "error", detail: "Pages introuvables — vérifier redirections" },
  { type: "Balises title dupliquées", count: 4, severity: "warn", detail: "Shopify collections et tags" },
  { type: "Images sans alt", count: 23, severity: "warn", detail: "Produits Rouge Pivoine" },
  { type: "Vitesse page mobile", count: 2, severity: "error", detail: "Score < 50 sur mobile" },
];

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SeoPage() {
  const totalTraffic = MOCK_SITES.reduce((s, x) => s + x.traffic, 0);
  const avgScore = Math.round(
    MOCK_SITES.filter((s) => s.score > 0).reduce((s, x) => s + x.score, 0) /
    MOCK_SITES.filter((s) => s.score > 0).length
  );
  const totalErrors = MOCK_SITES.reduce((s, x) => s + x.errors, 0);
  const totalTop10 = MOCK_SITES.reduce((s, x) => s + x.positions_top10, 0);

  return (
    <div style={{ maxWidth: 1100 }}>
      <PageHeader
        title="SEO Analytics"
        subtitle="Visibilité organique — Ex-Nihilo Agency & clients"
      />

      <MockBanner message="Données de démonstration. Brancher Google Search Console API + PageSpeed Insights pour les vraies métriques." />

      <InsetNotice
        icon="◱"
        text="Endpoint /api/seo non implémenté"
        detail="Interfaces : SeoSite, SeoPosition, CoreWebVital dans dashboard/lib/types.ts · Sources : GSC API, PageSpeed · Scope Codex P2"
        variant="muted"
      />

      {/* ── KPI globaux ── */}
      <div className="grid-auto-4" style={{ marginBottom: 16 }}>
        <StatCard
          label="Score SEO moyen"
          value={`${avgScore}/100`}
          sub="MOCK · 2 sites indexés"
          color={avgScore >= 70 ? "var(--green)" : "var(--yellow)"}
          size="lg"
        />
        <StatCard
          label="Trafic organique"
          value={totalTraffic.toLocaleString("fr-FR")}
          sub="MOCK · visites/mois"
          color="var(--blue)"
        />
        <StatCard
          label="Positions top 10"
          value={totalTop10}
          sub="MOCK · mots-clés"
          color="var(--green)"
        />
        <StatCard
          label="Erreurs critiques"
          value={totalErrors}
          sub="MOCK · à corriger"
          color={totalErrors > 5 ? "var(--red)" : "var(--yellow)"}
        />
      </div>

      {/* ── Sites ── */}
      <div style={{ marginBottom: 16 }}>
        <SectionLabel>Sites suivis</SectionLabel>
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          {MOCK_SITES.map((site, i) => {
            const noData = site.status === "nodata";
            return (
              <div
                key={site.name}
                style={{
                  padding: "14px 16px",
                  borderBottom: i < MOCK_SITES.length - 1 ? "1px solid var(--border)" : "none",
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  flexWrap: "wrap",
                  opacity: noData ? 0.5 : 1,
                }}
              >
                <div style={{ minWidth: 180, flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", fontFamily: "monospace" }}>
                    {site.name}
                  </div>
                  {noData && (
                    <div style={{ fontSize: 11, color: "var(--border)" }}>Pas encore indexé</div>
                  )}
                </div>

                {!noData && (
                  <>
                    <div style={{ width: 140 }}>
                      <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>
                        Score SEO
                      </div>
                      <Gauge value={site.score} />
                    </div>
                    <div style={{ textAlign: "center", minWidth: 70 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: "var(--blue)" }}>
                        {site.traffic.toLocaleString("fr-FR")}
                      </div>
                      <div style={{ fontSize: 10, color: "var(--muted)" }}>visites/mois</div>
                    </div>
                    <div style={{ textAlign: "center", minWidth: 60 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: "var(--green)" }}>
                        {site.positions_top10}
                      </div>
                      <div style={{ fontSize: 10, color: "var(--muted)" }}>top 10</div>
                    </div>
                    <div style={{ textAlign: "center", minWidth: 50 }}>
                      <div
                        style={{
                          fontSize: 18,
                          fontWeight: 700,
                          color: site.errors > 5 ? "var(--red)" : "var(--yellow)",
                        }}
                      >
                        {site.errors}
                      </div>
                      <div style={{ fontSize: 10, color: "var(--muted)" }}>erreurs</div>
                    </div>
                  </>
                )}

                {noData && (
                  <Badge label="Aucune donnée" variant="border" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid-auto-2" style={{ marginBottom: 16 }}>
        {/* ── Core Web Vitals ── */}
        <Card title="Core Web Vitals — ex-nihilo.agency · MOCK">
          {Object.entries(MOCK_CWV).map(([key, cwv]) => (
            <div
              key={key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "8px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <span
                style={{
                  fontSize: 10,
                  width: 7,
                  height: 7,
                  borderRadius: "50%",
                  background: cwv.ok ? "var(--green)" : "var(--red)",
                  flexShrink: 0,
                  display: "inline-block",
                }}
              />
              <span style={{ fontSize: 12, fontWeight: 600, minWidth: 48, color: "var(--text)", fontFamily: "monospace" }}>
                {key}
              </span>
              <span style={{ fontSize: 13, fontWeight: 700, flex: 1, color: cwv.ok ? "var(--green)" : "var(--red)" }}>
                {cwv.value}
              </span>
              <span style={{ fontSize: 11, color: "var(--border)" }}>cible {cwv.target}</span>
              <span
                style={{
                  fontSize: 10,
                  padding: "1px 6px",
                  borderRadius: 3,
                  background: cwv.ok ? "rgba(52,199,89,0.12)" : "rgba(255,69,58,0.12)",
                  color: cwv.ok ? "var(--green)" : "var(--red)",
                }}
              >
                {cwv.score}
              </span>
            </div>
          ))}
        </Card>

        {/* ── Erreurs ── */}
        <Card title="Erreurs à corriger — MOCK">
          {MOCK_ERRORS.map((err, i) => (
            <div
              key={i}
              style={{
                padding: "9px 0",
                borderBottom: i < MOCK_ERRORS.length - 1 ? "1px solid var(--border)" : "none",
                display: "flex",
                gap: 10,
                alignItems: "flex-start",
              }}
            >
              <span
                style={{
                  color: err.severity === "error" ? "var(--red)" : "var(--yellow)",
                  fontSize: 9,
                  marginTop: 4,
                  flexShrink: 0,
                }}
              >
                ●
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: "var(--text)", fontWeight: 500 }}>
                  {err.type}
                  <span
                    style={{
                      marginLeft: 8,
                      fontSize: 11,
                      color:
                        err.severity === "error" ? "var(--red)" : "var(--yellow)",
                    }}
                  >
                    ×{err.count}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
                  {err.detail}
                </div>
              </div>
            </div>
          ))}
        </Card>
      </div>

      {/* ── Positions ── */}
      <Card title="Mots-clés — top positions · MOCK" noPad>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Mot-clé", "Position", "Clics", "Impressions", "Tendance"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "10px 16px",
                      textAlign: h === "Mot-clé" ? "left" : "right",
                      fontSize: 10,
                      letterSpacing: 1,
                      textTransform: "uppercase",
                      color: "var(--muted)",
                      fontWeight: 600,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_POSITIONS.map((row, i) => {
                const trendColor =
                  row.trend === "up" ? "var(--green)" :
                  row.trend === "down" ? "var(--red)" :
                  "var(--border)";
                const trendIcon = row.trend === "up" ? "↑" : row.trend === "down" ? "↓" : "→";
                return (
                  <tr
                    key={i}
                    style={{
                      borderBottom:
                        i < MOCK_POSITIONS.length - 1 ? "1px solid var(--border)" : "none",
                    }}
                  >
                    <td style={{ padding: "10px 16px", color: "var(--text)" }}>{row.keyword}</td>
                    <td style={{ padding: "10px 16px", textAlign: "right" }}>
                      <span
                        style={{
                          fontWeight: 700,
                          color: row.position <= 3 ? "var(--green)" : row.position <= 10 ? "var(--text)" : "var(--muted)",
                        }}
                      >
                        {row.position}
                      </span>
                    </td>
                    <td style={{ padding: "10px 16px", textAlign: "right", color: "var(--text)" }}>
                      {row.clicks}
                    </td>
                    <td style={{ padding: "10px 16px", textAlign: "right", color: "var(--muted)" }}>
                      {row.impressions}
                    </td>
                    <td style={{ padding: "10px 16px", textAlign: "right" }}>
                      <span style={{ color: trendColor, fontWeight: 700 }}>{trendIcon}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ padding: "8px 16px", fontSize: 11, color: "var(--border)" }}>
          ⚠ MOCK — Connecter Google Search Console API pour les positions réelles
        </div>
      </Card>

      {/* ── Actions prioritaires — ATHOS ── */}
      <div style={{ marginTop: 16 }}>
        <SectionLabel>Actions SEO prioritaires — MOCK · Hiérarchie IA</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {[
            { priority: "P0", label: "Corriger les 4xx — 7 pages introuvables", impact: "critique", detail: "Redirections manquantes sur rouge-pivoine.fr · perte de jus SEO" },
            { priority: "P1", label: "Optimiser vitesse mobile — 2 pages < 50", impact: "élevé",    detail: "Score mobile critique — nuit au ranking Google · Lighthouse < 50" },
            { priority: "P1", label: "Alt text sur 23 images produit",           impact: "élevé",    detail: "Rouge Pivoine — images produits sans attribut alt" },
            { priority: "P2", label: "Dédupliquer les balises title — 4 pages",  impact: "moyen",    detail: "Collections et tags Shopify génèrent des titres identiques" },
            { priority: "P2", label: "Améliorer CLS (0.12 > cible 0.1)",         impact: "moyen",    detail: "Layout shift visible — probable image sans dimensions déclarées" },
          ].map((action, i) => {
            const col = action.impact === "critique" ? "var(--red)" : action.impact === "élevé" ? "var(--yellow)" : "var(--muted)";
            return (
              <div
                key={i}
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderLeft: `3px solid ${col}`,
                  borderRadius: 6,
                  padding: "10px 14px",
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-start",
                }}
              >
                <span style={{ fontSize: 10, fontWeight: 700, color: col, minWidth: 20, marginTop: 2 }}>{action.priority}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: "var(--text)", fontWeight: 500 }}>{action.label}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}>{action.detail}</div>
                </div>
                <Badge label={action.impact} variant={action.impact === "critique" ? "red" : action.impact === "élevé" ? "yellow" : "muted"} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
