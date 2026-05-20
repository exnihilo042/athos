import { athosPost } from "@/lib/athos";
import { SectionLabel, StatCard, Badge, PageHeader, InsetNotice } from "@/components/ui";
import type { CrmRuntimePayload, CrmClientRuntime } from "@/lib/types";

// ── Visual config ─────────────────────────────────────────────────────────────

type ClientStatus = string;
type AttentionLevel = string;

const STATUS_COLOR: Record<string, string> = {
  active:   "var(--green)",
  building: "var(--accent)",
  pending:  "var(--yellow)",
  prospect: "var(--blue)",
  blocked:  "var(--red)",
  done:     "var(--muted)",
  paused:   "var(--border)",
  unknown:  "var(--border)",
};

const STATUS_LABEL: Record<string, string> = {
  active:   "Actif",
  building: "En construction",
  pending:  "En attente",
  prospect: "Prospect",
  blocked:  "Bloqué",
  done:     "Terminé",
  paused:   "En pause",
  unknown:  "Inconnu",
};

const STATUS_BADGE_VARIANT: Record<string, "green" | "accent" | "yellow" | "blue" | "red" | "muted" | "border"> = {
  active:   "green",
  building: "accent",
  pending:  "yellow",
  prospect: "blue",
  blocked:  "red",
  done:     "muted",
  paused:   "border",
  unknown:  "border",
};

const ATTENTION_CONFIG: Record<string, { color: string; label: string; variant: "red" | "yellow" | "muted" }> = {
  high:   { color: "var(--red)",    label: "Urgent",   variant: "red" },
  medium: { color: "var(--yellow)", label: "À suivre", variant: "yellow" },
  normal: { color: "var(--muted)",  label: "OK",       variant: "muted" },
  low:    { color: "var(--muted)",  label: "OK",       variant: "muted" },
};

// ── Client card ───────────────────────────────────────────────────────────────

function ClientCard({ client }: { client: CrmClientRuntime }) {
  const statusColor = STATUS_COLOR[client.status] ?? STATUS_COLOR.unknown;
  const statusLabel = STATUS_LABEL[client.status] ?? client.status;
  const statusVariant = STATUS_BADGE_VARIANT[client.status] ?? "border";
  const ac = ATTENTION_CONFIG[client.attention] ?? ATTENTION_CONFIG.normal;

  return (
    <div
      style={{
        background: "var(--surface)",
        border: `1px solid ${client.blocked ? "rgba(255,69,58,0.25)" : "var(--border)"}`,
        borderLeft: `3px solid ${statusColor}`,
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
          <div style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap" }}>
            {(client.tags ?? []).map((tag) => (
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
        </div>
        <div style={{ display: "flex", gap: 5, alignItems: "center", flexShrink: 0 }}>
          <Badge label={ac.label} variant={ac.variant} dot />
          <Badge label={statusLabel} variant={statusVariant} />
        </div>
      </div>

      {/* Project */}
      {client.project && (
        <div style={{ fontSize: 12, color: "var(--text)" }}>
          <span style={{ color: "var(--border)", marginRight: 6 }}>◱</span>
          {client.project}
        </div>
      )}

      {/* Blocker */}
      {client.blocked && (
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
          <span>Projet bloqué</span>
        </div>
      )}

      {/* Next action */}
      {client.next_action && (
        <div style={{ fontSize: 11, display: "flex", gap: 6, color: "var(--accent)" }}>
          <span>→</span>
          <span style={{ flex: 1 }}>{client.next_action.slice(0, 120)}</span>
        </div>
      )}

      {/* Footer — source quality */}
      <div
        style={{
          paddingTop: 6,
          borderTop: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span
          style={{
            fontSize: 9,
            padding: "1px 6px",
            borderRadius: 20,
            background: "rgba(169,164,178,0.1)",
            color: "var(--border)",
            border: "1px solid var(--border)",
            fontFamily: "monospace",
          }}
        >
          source: mém. ATHOS · PARTIEL
        </span>
        {client.monthly_value != null ? (
          <span style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>
            {client.monthly_value.toLocaleString("fr-FR")} €/mois
          </span>
        ) : (
          <span style={{ fontSize: 11, color: "var(--border)" }}>valeur inconnue</span>
        )}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default async function CrmPage() {
  let data: CrmRuntimePayload | null = null;
  let fetchError = false;

  try {
    data = await athosPost<CrmRuntimePayload>("/api/crm");
  } catch {
    fetchError = true;
  }

  const clients = data?.clients ?? [];
  const active = data?.active ?? 0;
  const urgent = data?.urgent ?? 0;
  const blocked = data?.blocked ?? 0;
  const missingSources = data?.missing_sources ?? [];

  // Group by status
  const byStatus: Record<string, CrmClientRuntime[]> = {};
  for (const c of clients) {
    if (!byStatus[c.status]) byStatus[c.status] = [];
    byStatus[c.status].push(c);
  }

  const statusOrder = ["active", "building", "blocked", "pending", "prospect", "done"];
  const groups = statusOrder
    .filter((s) => byStatus[s]?.length > 0)
    .map((status) => ({ status, clients: byStatus[status] }));

  // Include any unlisted statuses
  for (const [status, list] of Object.entries(byStatus)) {
    if (!statusOrder.includes(status) && list.length > 0) {
      groups.push({ status, clients: list });
    }
  }

  return (
    <div style={{ maxWidth: 1000 }}>
      <PageHeader
        title="CRM / Clients"
        subtitle="Gestion relation client — Ex-Nihilo Agency"
      />

      {/* Partial data notice */}
      <InsetNotice
        icon="◾"
        text={
          fetchError
            ? "Endpoint /api/crm indisponible — HUB non joignable"
            : `Source : athos_projects.mem · Qualité : PARTIEL · ${clients.length} projet${clients.length > 1 ? "s" : ""} extraits`
        }
        detail={
          missingSources.length > 0
            ? `Données manquantes : ${missingSources.join(", ")}`
            : "Aucun outil CRM dédié connecté — les données proviennent de la mémoire ATHOS"
        }
        variant={fetchError ? "yellow" : "muted"}
      />

      {/* KPI */}
      <div className="grid-auto-4" style={{ marginBottom: 20 }}>
        <StatCard
          label="Projets extraits"
          value={clients.length}
          sub="PARTIEL · mémoire ATHOS"
          color="var(--text)"
          size="lg"
        />
        <StatCard
          label="Actifs"
          value={active}
          sub="PARTIEL · projets en cours"
          color={active > 0 ? "var(--green)" : "var(--muted)"}
        />
        <StatCard
          label="Attention requise"
          value={urgent}
          sub="PARTIEL · bloqués ou en attente"
          color={urgent > 0 ? "var(--red)" : "var(--green)"}
        />
        <StatCard
          label="Bloqués"
          value={blocked}
          sub="PARTIEL · nécessitent action"
          color={blocked > 0 ? "var(--yellow)" : "var(--green)"}
        />
      </div>

      {/* Clients par statut */}
      {groups.length === 0 ? (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "32px 24px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 20, color: "var(--border)", marginBottom: 8 }}>◾</div>
          <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 4 }}>
            {fetchError ? "HUB inaccessible" : "Aucun projet CRM extrait"}
          </div>
          <div style={{ fontSize: 11, color: "var(--border)" }}>
            {fetchError
              ? "Vérifier que le serveur ATHOS tourne sur :7474"
              : "Vérifier que athos_projects.mem contient des §proj: avec status et state"}
          </div>
        </div>
      ) : (
        groups.map(({ status, clients: groupClients }) => {
          const sc = { color: STATUS_COLOR[status] ?? "var(--muted)", label: STATUS_LABEL[status] ?? status };
          return (
            <div key={status} style={{ marginBottom: 20 }}>
              <SectionLabel count={groupClients.length}>
                <span style={{ color: sc.color }}>{sc.label}</span>
              </SectionLabel>
              <div className="grid-auto-2">
                {groupClients.map((client) => (
                  <ClientCard key={client.id} client={client} />
                ))}
              </div>
            </div>
          );
        })
      )}

      <div style={{ marginTop: 12, fontSize: 11, color: "var(--border)" }}>
        Source : /api/crm → athos_projects.mem · Qualité partielle — pipeline financier et historique relationnel non disponibles
      </div>
    </div>
  );
}
