import { athosPost } from "@/lib/athos";
import { Card, PageHeader, Badge } from "@/components/ui";

interface SettingsPayload {
  spend_policy?: {
    mode?: string;
    paid_api_enabled?: boolean;
    openai_enabled?: boolean;
    whisper_enabled?: boolean;
    skill_install_enabled?: boolean;
    autonomous_loop_enabled?: boolean;
    room_auto_respond?: boolean;
    room_auto_respond_engines?: string[];
    room_auto_coordination_rounds?: number;
    room_auto_work?: boolean;
    room_auto_work_review?: boolean;
  };
  security_policy?: {
    bind_host?: string;
    port?: number;
    token_required?: boolean;
    remote_token_required?: boolean;
    token_configured?: boolean;
    token_enforced_reason?: string;
    allow_any_write?: boolean;
    allowed_write_roots?: string[];
  };
  engine_order?: string;
  env?: Record<string, string>;
}

function Toggle({ on, label, envKey }: { on: boolean; label: string; envKey: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
      <div>
        <div style={{ fontSize: 13, color: "var(--text)" }}>{label}</div>
        <div style={{ fontSize: 11, color: "var(--border)", fontFamily: "monospace", marginTop: 2 }}>{envKey}</div>
      </div>
      <span style={{
        padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
        background: on ? "rgba(52,199,89,0.12)" : "rgba(255,69,58,0.12)",
        color: on ? "var(--green)" : "var(--red)",
        border: `1px solid ${on ? "rgba(52,199,89,0.25)" : "rgba(255,69,58,0.25)"}`,
      }}>
        {on ? "ON" : "OFF"}
      </span>
    </div>
  );
}

function EnvRow({ envKey, value }: { envKey: string; value: string }) {
  const isMasked = value === "***";
  const isEmpty = !value;
  return (
    <div style={{ display: "flex", gap: 12, padding: "6px 0", borderBottom: "1px solid var(--border)", alignItems: "baseline", flexWrap: "wrap" }}>
      <span style={{ fontFamily: "monospace", fontSize: 11, color: "var(--accent)", minWidth: 260, flexShrink: 0 }}>{envKey}</span>
      <span style={{
        fontFamily: "monospace", fontSize: 11,
        color: isMasked ? "var(--muted)" : isEmpty ? "var(--border)" : "var(--text)",
        wordBreak: "break-all",
      }}>
        {isMasked ? "●●●●●●●●" : isEmpty ? "(vide)" : value}
      </span>
    </div>
  );
}

export default async function SettingsPage() {
  let cfg: SettingsPayload = {};

  try {
    cfg = await athosPost<SettingsPayload>("/api/settings");
  } catch {}

  const sp = cfg.spend_policy ?? {};
  const sec = cfg.security_policy ?? {};
  const env = cfg.env ?? {};

  return (
    <div style={{ maxWidth: 900 }}>
      <PageHeader
        title="Paramètres"
        subtitle="Configuration ATHOS — lecture seule"
      >
        <Badge label="RÉEL" variant="green" />
        <span style={{ fontSize: 11, color: "var(--muted)", fontFamily: "monospace" }}>~/Sites/athos/.env</span>
      </PageHeader>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: 16, marginBottom: 16 }}>
        <Card title="Politique de dépense">
          <div style={{ marginBottom: 12 }}>
            <span style={{
              fontSize: 14, fontWeight: 700,
              color: sp.paid_api_enabled ? "var(--yellow)" : "var(--green)",
            }}>
              {sp.mode ?? "—"}
            </span>
          </div>
          <Toggle on={!!sp.paid_api_enabled} label="API payante autorisée" envKey="ATHOS_API_SPEND" />
          <Toggle on={!!sp.openai_enabled} label="OpenAI activé" envKey="OPENAI_ENABLED" />
          <Toggle on={!!sp.whisper_enabled} label="Whisper STT" envKey="WHISPER_ENABLED" />
          <Toggle on={!!sp.skill_install_enabled} label="Installation de skills" envKey="ATHOS_SKILL_INSTALL_ENABLED" />
          <Toggle on={!!sp.autonomous_loop_enabled} label="Boucle autonome" envKey="ATHOS_AUTONOMOUS_LOOP_ENABLED" />
        </Card>

        <Card title="Room — Réponse automatique">
          <Toggle on={!!sp.room_auto_respond} label="Auto-respond activé" envKey="ATHOS_ROOM_AUTO_RESPOND" />
          <Toggle on={!!sp.room_auto_work} label="Auto-work activé" envKey="ATHOS_ROOM_AUTO_WORK" />
          <Toggle on={!!sp.room_auto_work_review} label="Review auto-work" envKey="ATHOS_ROOM_AUTO_WORK_REVIEW" />
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
            Engines : <span style={{ color: "var(--text)", fontFamily: "monospace" }}>
              {(sp.room_auto_respond_engines ?? []).join(", ") || "—"}
            </span>
          </div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
            Coordination rounds : <span style={{ color: "var(--text)" }}>{sp.room_auto_coordination_rounds ?? "—"}</span>
          </div>
        </Card>

        <Card title="Sécurité">
          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Host</span>
              <span style={{ fontFamily: "monospace", fontSize: 12 }}>{sec.bind_host ?? "—"}:{sec.port ?? "—"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Token configuré</span>
              <span style={{ color: sec.token_configured ? "var(--green)" : "var(--red)", fontSize: 12 }}>
                {sec.token_configured ? "oui" : "non"}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Token enforced</span>
              <span style={{ color: sec.token_required ? "var(--green)" : "var(--muted)", fontSize: 12 }}>
                {sec.token_enforced_reason ?? "—"}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ color: "var(--muted)" }}>Allow any write</span>
              <span style={{ color: sec.allow_any_write ? "var(--yellow)" : "var(--green)", fontSize: 12 }}>
                {sec.allow_any_write ? "oui (permissif)" : "non (restreint)"}
              </span>
            </div>
          </div>
          {(sec.allowed_write_roots ?? []).length > 0 && (
            <div style={{ marginTop: 12, fontSize: 11, color: "var(--muted)" }}>
              Write roots :
              {(sec.allowed_write_roots ?? []).map((r, i) => (
                <div key={i} style={{ fontFamily: "monospace", color: "var(--text)", marginTop: 2, wordBreak: "break-all" }}>{r}</div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Ordre des moteurs">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {(cfg.engine_order ?? "").split(",").filter(Boolean).map((e, i) => (
              <div key={e} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span style={{ fontSize: 10, color: "var(--border)", minWidth: 16, textAlign: "right" }}>{i + 1}</span>
                <span style={{ fontSize: 13, color: i === 0 ? "var(--accent)" : "var(--text)", fontWeight: i === 0 ? 600 : 400 }}>{e.trim()}</span>
                {i === 0 && <span style={{ fontSize: 10, color: "var(--accent)", opacity: 0.7 }}>primaire</span>}
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, fontSize: 11, color: "var(--border)", fontFamily: "monospace" }}>ATHOS_ENGINE_ORDER</div>
        </Card>
      </div>

      <Card title="Variables d'environnement (.env)">
        {Object.keys(env).length === 0 ? (
          <span style={{ color: "var(--muted)", fontSize: 13 }}>Aucune variable chargée</span>
        ) : (
          <div style={{ maxHeight: 340, overflowY: "auto" }}>
            {Object.entries(env).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => (
              <EnvRow key={k} envKey={k} value={v} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
