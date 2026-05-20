"use client";

import { useState } from "react";
import { WizardStepHeader, SocialChannelPill, IntegrationBadge } from "@/components/ui";
import Link from "next/link";

// ── Types ─────────────────────────────────────────────────────────────────────

type ProjectType = "shopify" | "saas" | "mobile" | "site" | "agency" | "other";
type ProjectStatus = "active" | "building" | "pending";
type Autonomy = "supervised" | "semi-auto" | "autonomous";

interface WizardState {
  // Step 1 — Identity
  name: string;
  type: ProjectType;
  description: string;
  status: ProjectStatus;
  priority: string;

  // Step 2 — Digital presence
  site: string;
  domain: string;
  repo: string;
  drive: string;

  // Step 3 — Business tools
  shopify: string;
  stripe: boolean;
  analytics: string;
  gsc: string;
  crm: string;
  hosting: string;
  monitoring: string;

  // Step 4 — Social channels
  instagram: string;
  tiktok: string;
  linkedin: string;
  x: string;
  youtube: string;
  facebook: string;
  pinterest: string;
  newsletter: string;

  // Step 5 — Goals
  goal_ca: string;
  goal_traffic: string;
  goal_leads: string;
  goal_orders: string;
  goal_seo_top10: string;
  goal_content_per_week: string;

  // Step 6 — Agents
  agent_seo: boolean;
  agent_dev: boolean;
  agent_finance: boolean;
  agent_content: boolean;
  agent_automation: boolean;
  agent_autonomy: Autonomy;
}

const INITIAL: WizardState = {
  name: "", type: "shopify", description: "", status: "active", priority: "3",
  site: "", domain: "", repo: "", drive: "",
  shopify: "", stripe: false, analytics: "", gsc: "", crm: "", hosting: "", monitoring: "",
  instagram: "", tiktok: "", linkedin: "", x: "", youtube: "", facebook: "", pinterest: "", newsletter: "",
  goal_ca: "", goal_traffic: "", goal_leads: "", goal_orders: "", goal_seo_top10: "", goal_content_per_week: "",
  agent_seo: false, agent_dev: true, agent_finance: false, agent_content: false, agent_automation: false,
  agent_autonomy: "supervised",
};

const STEPS = ["Identité", "Présence", "Outils", "Réseaux", "Objectifs", "Agents", "Récap"];

const TYPE_OPTIONS: { value: ProjectType; label: string; icon: string }[] = [
  { value: "shopify",  label: "Shopify",       icon: "◼" },
  { value: "saas",     label: "SaaS",           icon: "◳" },
  { value: "mobile",   label: "Mobile",         icon: "◾" },
  { value: "site",     label: "Site vitrine",   icon: "◱" },
  { value: "agency",   label: "Agence",         icon: "◈" },
  { value: "other",    label: "Autre",          icon: "◻" },
];

const PRIORITY_OPTIONS = ["0", "1", "2", "3", "4", "5"].map((p) => ({
  value: p,
  label: `P${p}${p === "0" ? " — critique" : p === "1" ? " — urgent" : p === "2" ? " — haut" : p === "3" ? " — normal" : p === "4" ? " — bas" : " — backlog"}`,
}));

// ── Shared input style ─────────────────────────────────────────────────────────

const INPUT_STYLE: React.CSSProperties = {
  width: "100%",
  background: "var(--surface-2)",
  border: "1px solid var(--border)",
  borderRadius: 6,
  padding: "8px 12px",
  color: "var(--text)",
  fontSize: 13,
  outline: "none",
  boxSizing: "border-box",
};

const LABEL_STYLE: React.CSSProperties = {
  fontSize: 11,
  color: "var(--muted)",
  letterSpacing: 0.5,
  marginBottom: 6,
  display: "block",
};

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={LABEL_STYLE}>{label}</label>
      {children}
    </div>
  );
}

function TextInput({
  value,
  onChange,
  placeholder,
  mono,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  mono?: boolean;
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{ ...INPUT_STYLE, fontFamily: mono ? "monospace" : undefined }}
    />
  );
}

function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 12px",
        background: "var(--surface-2)",
        borderRadius: 6,
        cursor: "pointer",
        marginBottom: 6,
      }}
      onClick={() => onChange(!checked)}
    >
      <span style={{ fontSize: 13, color: "var(--text)" }}>{label}</span>
      <span
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: checked ? "var(--green)" : "var(--border)",
          background: checked ? "rgba(52,199,89,0.12)" : "rgba(42,41,49,0.6)",
          border: `1px solid ${checked ? "rgba(52,199,89,0.3)" : "var(--border)"}`,
          padding: "2px 8px",
          borderRadius: 10,
        }}
      >
        {checked ? "ON" : "OFF"}
      </span>
    </div>
  );
}

// ── Steps ─────────────────────────────────────────────────────────────────────

function Step1({ state, set }: { state: WizardState; set: (s: Partial<WizardState>) => void }) {
  return (
    <div>
      <Field label="Nom du projet *">
        <TextInput value={state.name} onChange={(v) => set({ name: v })} placeholder="Ex : Rouge Pivoine" />
      </Field>

      <Field label="Type de projet">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {TYPE_OPTIONS.map((t) => (
            <div
              key={t.value}
              onClick={() => set({ type: t.value })}
              style={{
                padding: "10px 12px",
                background: state.type === t.value ? "rgba(120,60,255,0.15)" : "var(--surface-2)",
                border: `1px solid ${state.type === t.value ? "var(--accent)" : "var(--border)"}`,
                borderRadius: 6,
                cursor: "pointer",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 16, color: state.type === t.value ? "var(--accent)" : "var(--muted)", marginBottom: 4 }}>{t.icon}</div>
              <div style={{ fontSize: 12, color: state.type === t.value ? "var(--accent)" : "var(--text)", fontWeight: 500 }}>{t.label}</div>
            </div>
          ))}
        </div>
      </Field>

      <Field label="Description (optionnel)">
        <textarea
          value={state.description}
          onChange={(e) => set({ description: e.target.value })}
          placeholder="Courte description du projet…"
          rows={3}
          style={{ ...INPUT_STYLE, resize: "vertical", fontFamily: "inherit" }}
        />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="Statut initial">
          <select value={state.status} onChange={(e) => set({ status: e.target.value as ProjectStatus })} style={INPUT_STYLE}>
            <option value="active">Actif</option>
            <option value="building">En construction</option>
            <option value="pending">En attente</option>
          </select>
        </Field>
        <Field label="Priorité">
          <select value={state.priority} onChange={(e) => set({ priority: e.target.value })} style={INPUT_STYLE}>
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </Field>
      </div>
    </div>
  );
}

function Step2({ state, set }: { state: WizardState; set: (s: Partial<WizardState>) => void }) {
  return (
    <div>
      <Field label="URL du site">
        <TextInput value={state.site} onChange={(v) => set({ site: v })} placeholder="https://rouge-pivoine.fr" mono />
      </Field>
      <Field label="Domaine principal">
        <TextInput value={state.domain} onChange={(v) => set({ domain: v })} placeholder="rouge-pivoine.fr" mono />
      </Field>
      <Field label="Repository GitHub">
        <TextInput value={state.repo} onChange={(v) => set({ repo: v })} placeholder="https://github.com/exnihilo042/..." mono />
      </Field>
      <Field label="Dossier Google Drive">
        <TextInput value={state.drive} onChange={(v) => set({ drive: v })} placeholder="Mon Drive/..." mono />
      </Field>
    </div>
  );
}

function Step3({ state, set }: { state: WizardState; set: (s: Partial<WizardState>) => void }) {
  return (
    <div>
      <Field label="Shopify (URL store)">
        <TextInput value={state.shopify} onChange={(v) => set({ shopify: v })} placeholder="rouge-pivoine.myshopify.com" mono />
      </Field>
      <Toggle checked={state.stripe} onChange={(v) => set({ stripe: v })} label="Stripe configuré" />
      <div style={{ height: 10 }} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="Google Analytics (ID)">
          <TextInput value={state.analytics} onChange={(v) => set({ analytics: v })} placeholder="G-XXXXXXXXXX" mono />
        </Field>
        <Field label="Google Search Console">
          <TextInput value={state.gsc} onChange={(v) => set({ gsc: v })} placeholder="rouge-pivoine.fr" mono />
        </Field>
        <Field label="CRM">
          <TextInput value={state.crm} onChange={(v) => set({ crm: v })} placeholder="Dolibarr / Notion / ..." />
        </Field>
        <Field label="Hébergement">
          <TextInput value={state.hosting} onChange={(v) => set({ hosting: v })} placeholder="OVH / Vercel / ..." />
        </Field>
      </div>
      <Field label="Endpoint monitoring">
        <TextInput value={state.monitoring} onChange={(v) => set({ monitoring: v })} placeholder="https://status.rouge-pivoine.fr" mono />
      </Field>
    </div>
  );
}

const SOCIALS: { key: keyof WizardState; label: string }[] = [
  { key: "instagram", label: "Instagram" },
  { key: "tiktok",    label: "TikTok" },
  { key: "linkedin",  label: "LinkedIn" },
  { key: "x",         label: "X / Twitter" },
  { key: "youtube",   label: "YouTube" },
  { key: "facebook",  label: "Facebook" },
  { key: "pinterest", label: "Pinterest" },
  { key: "newsletter",label: "Newsletter" },
];

function Step4({ state, set }: { state: WizardState; set: (s: Partial<WizardState>) => void }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>
        Laisser vide les réseaux non utilisés pour ce projet.
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {SOCIALS.map(({ key, label }) => (
          <Field key={key} label={label}>
            <TextInput
              value={state[key] as string}
              onChange={(v) => set({ [key]: v })}
              placeholder={key === "newsletter" ? "Brevo / Mailchimp / ..." : `@handle`}
            />
          </Field>
        ))}
      </div>
    </div>
  );
}

function Step5({ state, set }: { state: WizardState; set: (s: Partial<WizardState>) => void }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>
        Objectifs mensuels cibles. Laisser vide si non applicable.
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="CA mensuel cible (€)">
          <TextInput value={state.goal_ca} onChange={(v) => set({ goal_ca: v })} placeholder="2000" />
        </Field>
        <Field label="Trafic organique (visites/mois)">
          <TextInput value={state.goal_traffic} onChange={(v) => set({ goal_traffic: v })} placeholder="5000" />
        </Field>
        <Field label="Leads mensuels">
          <TextInput value={state.goal_leads} onChange={(v) => set({ goal_leads: v })} placeholder="20" />
        </Field>
        <Field label="Commandes mensuelles">
          <TextInput value={state.goal_orders} onChange={(v) => set({ goal_orders: v })} placeholder="50" />
        </Field>
        <Field label="Positions top 10 SEO (n° mots-clés)">
          <TextInput value={state.goal_seo_top10} onChange={(v) => set({ goal_seo_top10: v })} placeholder="15" />
        </Field>
        <Field label="Cadence contenu (posts/semaine)">
          <TextInput value={state.goal_content_per_week} onChange={(v) => set({ goal_content_per_week: v })} placeholder="3" />
        </Field>
      </div>
    </div>
  );
}

const AGENTS: { key: keyof WizardState; label: string; desc: string }[] = [
  { key: "agent_seo",        label: "SEO Agent",         desc: "Audits, positions, recommandations" },
  { key: "agent_dev",        label: "Dev Agent",         desc: "Code, PRs, déploiements, tests" },
  { key: "agent_finance",    label: "Finance Agent",     desc: "CA, marges, facturation" },
  { key: "agent_content",    label: "Content Agent",     desc: "Rédaction, réseaux, brief créatif" },
  { key: "agent_automation", label: "Automation Agent",  desc: "Scripts, workflows, cron" },
];

function Step6({ state, set }: { state: WizardState; set: (s: Partial<WizardState>) => void }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}>
        Sélectionner les agents ATHOS à assigner à ce projet.
      </div>
      {AGENTS.map(({ key, label, desc }) => (
        <div
          key={key}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "10px 14px",
            background: "var(--surface-2)",
            border: `1px solid ${state[key] ? "rgba(120,60,255,0.3)" : "var(--border)"}`,
            borderRadius: 6,
            marginBottom: 8,
            cursor: "pointer",
          }}
          onClick={() => set({ [key]: !state[key] })}
        >
          <span style={{ fontSize: 12, fontWeight: 600, color: state[key] ? "var(--accent)" : "var(--muted)", minWidth: 100 }}>
            {label}
          </span>
          <span style={{ fontSize: 11, color: "var(--muted)", flex: 1 }}>{desc}</span>
          <span style={{
            fontSize: 10, fontWeight: 600,
            color: state[key] ? "var(--green)" : "var(--border)",
            background: state[key] ? "rgba(52,199,89,0.12)" : "transparent",
            border: `1px solid ${state[key] ? "rgba(52,199,89,0.3)" : "var(--border)"}`,
            padding: "2px 8px", borderRadius: 10,
          }}>
            {state[key] ? "ON" : "OFF"}
          </span>
        </div>
      ))}

      <div style={{ marginTop: 16 }}>
        <label style={LABEL_STYLE}>Degré d&apos;autonomie global</label>
        <div style={{ display: "flex", gap: 8 }}>
          {([["supervised", "Supervisé"], ["semi-auto", "Semi-auto"], ["autonomous", "Autonome"]] as [Autonomy, string][]).map(([val, label]) => (
            <div
              key={val}
              onClick={() => set({ agent_autonomy: val })}
              style={{
                flex: 1, padding: "8px 12px", textAlign: "center",
                background: state.agent_autonomy === val ? "rgba(120,60,255,0.15)" : "var(--surface-2)",
                border: `1px solid ${state.agent_autonomy === val ? "var(--accent)" : "var(--border)"}`,
                borderRadius: 6, cursor: "pointer", fontSize: 12,
                color: state.agent_autonomy === val ? "var(--accent)" : "var(--muted)",
              }}
            >
              {label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Step7({ state }: { state: WizardState }) {
  const integrations = [
    state.shopify && { tool: "Shopify", status: "configured" as const, ref: state.shopify },
    state.stripe  && { tool: "Stripe",  status: "configured" as const },
    state.analytics && { tool: "Google Analytics", status: "configured" as const, ref: state.analytics },
    state.gsc     && { tool: "Search Console", status: "configured" as const, ref: state.gsc },
    state.hosting && { tool: "Hébergement", status: "configured" as const, ref: state.hosting },
    state.repo    && { tool: "GitHub", status: "configured" as const, ref: state.repo },
  ].filter(Boolean) as { tool: string; status: "configured"; ref?: string }[];

  const socials = [
    state.instagram && { platform: "instagram", handle: state.instagram },
    state.tiktok    && { platform: "tiktok",    handle: state.tiktok },
    state.linkedin  && { platform: "linkedin",  handle: state.linkedin },
    state.x         && { platform: "x",         handle: state.x },
    state.youtube   && { platform: "youtube",   handle: state.youtube },
    state.newsletter && { platform: "newsletter", handle: state.newsletter },
  ].filter(Boolean) as { platform: string; handle: string }[];

  const agents = AGENTS.filter((a) => state[a.key]);

  return (
    <div>
      {/* Header projet */}
      <div style={{
        background: "rgba(120,60,255,0.08)",
        border: "1px solid rgba(120,60,255,0.2)",
        borderRadius: 8,
        padding: "16px 20px",
        marginBottom: 20,
      }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
          {state.name || "(nom non défini)"}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <span style={{ fontSize: 11, padding: "2px 8px", background: "rgba(120,60,255,0.2)", color: "var(--accent)", borderRadius: 4 }}>
            {TYPE_OPTIONS.find((t) => t.value === state.type)?.icon} {state.type}
          </span>
          <span style={{ fontSize: 11, padding: "2px 8px", background: "var(--surface-2)", color: "var(--muted)", borderRadius: 4 }}>
            P{state.priority}
          </span>
          <span style={{ fontSize: 11, padding: "2px 8px", background: "rgba(52,199,89,0.12)", color: "var(--green)", borderRadius: 4 }}>
            {state.status}
          </span>
        </div>
        {state.description && (
          <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 10 }}>{state.description}</div>
        )}
      </div>

      {/* Résumé */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Intégrations", value: integrations.length, suffix: "configurées", color: integrations.length > 0 ? "var(--blue)" : "var(--border)" },
          { label: "Réseaux", value: socials.length, suffix: "configurés", color: socials.length > 0 ? "var(--green)" : "var(--border)" },
          { label: "Agents", value: agents.length, suffix: "assignés", color: agents.length > 0 ? "var(--accent)" : "var(--border)" },
          { label: "Objectifs", value: [state.goal_ca, state.goal_traffic, state.goal_leads, state.goal_orders].filter(Boolean).length, suffix: "définis", color: "var(--yellow)" },
        ].map(({ label, value, suffix, color }) => (
          <div key={label} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, padding: "12px 14px" }}>
            <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>{label} {suffix}</div>
          </div>
        ))}
      </div>

      {integrations.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8, letterSpacing: 0.5, textTransform: "uppercase" }}>Intégrations</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {integrations.map((i) => (
              <IntegrationBadge key={i.tool} tool={i.tool} status={i.status} ref={i.ref} />
            ))}
          </div>
        </div>
      )}

      {socials.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8, letterSpacing: 0.5, textTransform: "uppercase" }}>Réseaux</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {socials.map((s) => <SocialChannelPill key={s.platform} platform={s.platform} handle={s.handle} />)}
          </div>
        </div>
      )}

      {agents.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8, letterSpacing: 0.5, textTransform: "uppercase" }}>Agents assignés</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {agents.map((a) => (
              <span key={a.key} style={{ fontSize: 11, padding: "3px 10px", background: "rgba(120,60,255,0.12)", color: "var(--accent)", border: "1px solid rgba(120,60,255,0.25)", borderRadius: 20 }}>
                {a.label}
              </span>
            ))}
          </div>
          <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 6 }}>Autonomie : {state.agent_autonomy}</div>
        </div>
      )}

      {/* Prototype notice */}
      <div style={{
        marginTop: 20,
        padding: "10px 14px",
        background: "rgba(255,214,10,0.08)",
        border: "1px solid rgba(255,214,10,0.2)",
        borderRadius: 6,
        fontSize: 11,
        color: "var(--yellow)",
      }}>
        ⚠ Prototype frontend — persistance backend à brancher · Endpoint proposé : POST /api/projects/create · Scope Codex P2
      </div>
    </div>
  );
}

// ── Main wizard ───────────────────────────────────────────────────────────────

export default function NewProjectPage() {
  const [step, setStep] = useState(0);
  const [state, setState] = useState<WizardState>(INITIAL);
  const [submitted, setSubmitted] = useState(false);

  const set = (partial: Partial<WizardState>) => setState((s) => ({ ...s, ...partial }));

  const canNext = step === 0 ? state.name.trim().length > 0 : true;

  if (submitted) {
    return (
      <div style={{ maxWidth: 600, padding: "60px 0", textAlign: "center" }}>
        <div style={{ fontSize: 32, color: "var(--green)", marginBottom: 16 }}>✓</div>
        <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text)", marginBottom: 8 }}>
          Projet configuré
        </div>
        <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 24 }}>
          <strong style={{ color: "var(--accent)" }}>{state.name}</strong> a été configuré côté frontend.
          La persistance backend est à brancher via <code style={{ fontFamily: "monospace", color: "var(--border)" }}>POST /api/projects/create</code>.
        </div>
        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          <Link href="/dashboard/projects" style={{ textDecoration: "none" }}>
            <button style={{ padding: "8px 20px", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13 }}>
              ← Retour aux projets
            </button>
          </Link>
          <button
            onClick={() => { setState(INITIAL); setStep(0); setSubmitted(false); }}
            style={{ padding: "8px 20px", background: "var(--surface-2)", color: "var(--muted)", border: "1px solid var(--border)", borderRadius: 6, cursor: "pointer", fontSize: 13 }}
          >
            Créer un autre
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 700 }}>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
          <Link href="/dashboard/projects" style={{ fontSize: 12, color: "var(--muted)", textDecoration: "none" }}>
            ← Projets
          </Link>
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: "var(--text)", margin: 0, marginBottom: 4 }}>
          Nouveau projet
        </h1>
        <p style={{ fontSize: 13, color: "var(--muted)", margin: 0 }}>
          Project Control Center ATHOS — Configurer un nouveau projet pilotable
        </p>
      </div>

      {/* Step indicator */}
      <WizardStepHeader steps={STEPS} current={step} />

      {/* Step content */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "24px",
        marginBottom: 16,
        minHeight: 320,
      }}>
        {step === 0 && <Step1 state={state} set={set} />}
        {step === 1 && <Step2 state={state} set={set} />}
        {step === 2 && <Step3 state={state} set={set} />}
        {step === 3 && <Step4 state={state} set={set} />}
        {step === 4 && <Step5 state={state} set={set} />}
        {step === 5 && <Step6 state={state} set={set} />}
        {step === 6 && <Step7 state={state} />}
      </div>

      {/* Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          style={{
            padding: "8px 20px",
            background: "var(--surface-2)",
            color: step === 0 ? "var(--border)" : "var(--muted)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            cursor: step === 0 ? "default" : "pointer",
            fontSize: 13,
          }}
        >
          ← Précédent
        </button>

        <span style={{ fontSize: 11, color: "var(--border)" }}>{step + 1} / {STEPS.length}</span>

        {step < STEPS.length - 1 ? (
          <button
            onClick={() => canNext && setStep((s) => Math.min(STEPS.length - 1, s + 1))}
            disabled={!canNext}
            style={{
              padding: "8px 20px",
              background: canNext ? "var(--accent)" : "var(--surface-2)",
              color: canNext ? "#fff" : "var(--border)",
              border: "none",
              borderRadius: 6,
              cursor: canNext ? "pointer" : "default",
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            Suivant →
          </button>
        ) : (
          <button
            onClick={() => setSubmitted(true)}
            disabled={!state.name.trim()}
            style={{
              padding: "8px 20px",
              background: state.name.trim() ? "var(--green)" : "var(--surface-2)",
              color: state.name.trim() ? "#fff" : "var(--border)",
              border: "none",
              borderRadius: 6,
              cursor: state.name.trim() ? "pointer" : "default",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            Créer le projet
          </button>
        )}
      </div>
    </div>
  );
}
