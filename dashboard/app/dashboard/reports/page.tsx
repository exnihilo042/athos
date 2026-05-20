import { athosPost } from "@/lib/athos";

interface ReportPayload {
  brief?: string;
  date?: string;
  sections?: { title?: string; content?: string }[];
}

export default async function ReportsPage() {
  let report: ReportPayload = {};

  try {
    report = await athosPost<ReportPayload>("/api/report", { type: "daily" });
  } catch {}

  return (
    <div style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: 22, fontWeight: 600, marginBottom: 6 }}>Rapports</h1>
      <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 24 }}>
        Daily brief · Récapitulatifs session
      </p>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: 24,
        }}
      >
        {report.brief ? (
          <>
            {report.date && (
              <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 16, letterSpacing: 1 }}>
                {report.date}
              </div>
            )}
            <pre
              style={{
                fontSize: 13,
                color: "var(--text)",
                whiteSpace: "pre-wrap",
                lineHeight: 1.6,
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {report.brief}
            </pre>
          </>
        ) : (
          <>
            <div style={{ color: "var(--muted)", fontSize: 13, marginBottom: 16 }}>
              Aucun rapport disponible. Générez le daily brief via le terminal ATHOS.
            </div>
            <div
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 5,
                padding: "10px 14px",
                fontSize: 12,
                fontFamily: "monospace",
                color: "var(--muted)",
              }}
            >
              curl -X POST http://localhost:7474/api/report -H &quot;Authorization: Bearer $TOKEN&quot; -d &apos;{"{\"type\":\"daily\"}"}&apos;
            </div>
          </>
        )}
      </div>
    </div>
  );
}
