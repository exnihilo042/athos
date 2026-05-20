/**
 * ATHOS Dashboard — TypeScript contracts
 *
 * This file is the authoritative source for all API response types used
 * across the dashboard. It also declares future interfaces for features
 * reserved for Codex implementation.
 *
 * Status annotations:
 *   [REAL]   — endpoint exists, data is live
 *   [MOCK]   — placeholder, UI built, no real data source yet
 *   [CODEX]  — reserved for Codex implementation (do not implement client-side)
 *   [CLAUDE] — frontend/presentation layer, Claude scope
 */

// ────────────────────────────────────────────────────────────────────────────
// ATHOS HUB — Core status & session  [REAL]
// Source: POST /api/status
// ────────────────────────────────────────────────────────────────────────────

export interface SpendPolicy {
  mode: string;
  paid_api_enabled: boolean;
  openai_enabled: boolean;
  whisper_enabled: boolean;
  skill_install_enabled: boolean;
  autonomous_loop_enabled: boolean;
  room_auto_respond: boolean;
  room_auto_respond_engines: string[];
  room_auto_coordination_rounds: number;
  room_auto_work: boolean;
  room_auto_work_review: boolean;
}

export interface SessionStatus {
  file: string;
  events: number;
  exchanges: number;
  actions: number;
  summaries: number;
  attaches: number;
  delegates: number;
  reports: number;
  recent_summary: string;
  checkpoint: { goal: string; tasks: string[] };
  last_event: { id: string; ts: string; type: string; engine: string };
}

export interface CapabilityGraphSummary {
  nodes: number;
  edges: number;
  available_nodes: number;
  available_engines: string[];
  offline_ready_nodes: number;
  interconnection_score: number;
  austere_mode_ready: boolean;
}

export interface AthosStatus {
  engine: string;
  degraded: boolean;
  available: string[];
  budget: number;
  spend_policy: SpendPolicy;
  session: SessionStatus;
  capability_graph: {
    principle: string;
    summary: CapabilityGraphSummary;
    reuse_policy: string[];
  };
  server_runtime?: {
    pid: number;
    uptime_seconds: number;
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Capability graph  [REAL]
// Source: POST /api/capability_graph
// ────────────────────────────────────────────────────────────────────────────

export type NodeKind =
  | "identity" | "engine" | "memory" | "capability" | "guardrail"
  | "local_tool" | "protocol" | "skill" | "sync" | "device"
  | "hardware" | "model_profile" | "review_stage" | "external_source"
  | "academic_source" | "transport";

export type NodeStatus =
  | "active" | "ok" | "clear" | "available" | "configured"
  | "integrated" | "referenced" | "planned" | "missing" | "blocked_by_zero_spend";

export type RiskLevel = "low" | "medium" | "high";
export type CostLevel = "free" | "low" | "medium" | "high";

export interface CapabilityNode {
  id: string;
  kind: NodeKind;
  label: string;
  status: NodeStatus;
  offline: boolean;
  risk: RiskLevel;
  cost: CostLevel;
  tags?: string[];
  meta?: Record<string, unknown>;
}

export interface CapabilityGraph {
  nodes: CapabilityNode[];
  principle: string;
  summary: CapabilityGraphSummary;
}

// ────────────────────────────────────────────────────────────────────────────
// Observability  [REAL]
// Source: POST /api/observability
// ────────────────────────────────────────────────────────────────────────────

export interface FailoverEvent {
  ts: string;
  name: string;
  label: string;
  result: string;
  engine: string;
  context_hash: string;
}

export interface PortInfo {
  command: string;
  pid: number;
  user: string;
  name: string;
  reason: string;
  stoppable: boolean;
}

export interface MemoryFileInfo {
  name: string;
  exists: boolean;
  size: number;
  lines: number;
  last_line: string;
  updated_at: string;
}

export interface ObservabilityPayload {
  timestamp: string;
  git: { root: string; branch: string; head: string; dirty: string[]; remote: string };
  drive: { path: string; exists: boolean; memory_files: string[] };
  server_runtime: { pid: number; started_at: string; uptime_seconds: number; host: string; port: number };
  ports: PortInfo[];
  failover: FailoverEvent[];
  memory: {
    root: string;
    exists: boolean;
    canonical_files: MemoryFileInfo[];
    missing: string[];
    ok: boolean;
  };
  summary: {
    listening_ports: number;
    launchd_jobs: number;
    agent_processes: number;
    attached_engines: number;
    sync_pending: number;
    memory_missing: number;
    local_tools: number;
    failover_events: number;
    loop_running: boolean;
    installed_skills: number;
    devices: number;
    server_pid: number;
    capability_graph_nodes: number;
    capability_graph_edges: number;
    capability_graph_score: number;
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Room  [REAL]
// Source: POST /api/conversation, POST /api/message
// ────────────────────────────────────────────────────────────────────────────

export type RoomActor = "clement" | "claude" | "claude_code" | "codex" | "chatgpt_plus" | "athos";
export type RoomMessageType = "message" | "action" | "result" | "error" | "report" | "checkpoint" | "work" | "summary";

export interface RoomEntry {
  id: string;
  ts: string;
  actor: RoomActor;
  type: RoomMessageType;
  content: string;
  status?: string;
  task_id?: string;
  meta?: Record<string, unknown>;
}

export interface RoomThread {
  thread: RoomEntry[];
  summary: { total: number; task_id?: string };
}

// ────────────────────────────────────────────────────────────────────────────
// Settings  [REAL]
// Source: POST /api/settings
// ────────────────────────────────────────────────────────────────────────────

export interface SecurityPolicy {
  bind_host: string;
  port: number;
  token_required: boolean;
  remote_token_required: boolean;
  token_configured: boolean;
  token_enforced_reason: string;
  allow_any_write: boolean;
  allowed_write_roots: string[];
}

export interface AthosSettings {
  spend_policy: SpendPolicy;
  security_policy: SecurityPolicy;
  engine_order: string;
  env: Record<string, string>;
}

// ────────────────────────────────────────────────────────────────────────────
// Projects  [REAL — parsed from athos_projects.mem]
// Source: POST /api/projects
// ────────────────────────────────────────────────────────────────────────────

export interface Project {
  name: string;
  status?: "active" | "building" | "pending" | "done";
  priority?: string;
  stack?: string;
  local?: string;
  state?: string;
  next?: string;
  blocker?: string;
  memory?: string;
  store?: string;
  repo?: string;
  branch?: string;
  [key: string]: string | undefined;
}

// ────────────────────────────────────────────────────────────────────────────
// Task Queue  [CODEX] — reserved, do not implement frontend logic
// Source: POST /api/tasks (implemented by Codex — core/task_queue.py)
// ────────────────────────────────────────────────────────────────────────────

export type TaskStatus = "pending" | "running" | "done" | "failed" | "cancelled";
export type TaskPriority = "low" | "normal" | "high" | "critical";

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  engine?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: string;
  error?: string;
  meta?: Record<string, unknown>;
}

export interface TaskQueue {
  tasks: Task[];
  summary: {
    total: number;
    pending: number;
    running: number;
    done: number;
    failed: number;
  };
}

// ────────────────────────────────────────────────────────────────────────────
// Finances  [MOCK → future]
// Source: /api/finances — not yet implemented
// Candidates: Stripe API, Shopify Admin API, Dolibarr
// ────────────────────────────────────────────────────────────────────────────

export interface FinancesSummary {
  period: string;
  ca: number;
  ventes_nettes: number;
  commandes: number;
  marge_pct: number;
  commissions: number;
  resultat_net: number;
  currency: string;
}

export interface RevenueDataPoint {
  label: string;
  value: number;
}

export interface ProjectRevenue {
  name: string;
  type: string;
  amount: number;
  status: "facturé" | "en cours" | "devis" | "annulé";
}

// ────────────────────────────────────────────────────────────────────────────
// SEO Analytics  [MOCK → future]
// Source: Google Search Console API, PageSpeed Insights API
// ────────────────────────────────────────────────────────────────────────────

export interface SeoSite {
  name: string;
  score: number;
  traffic: number;
  positions_top10: number;
  errors: number;
  status: "ok" | "warn" | "error" | "nodata";
}

export interface CoreWebVital {
  value: string;
  score: number;
  target: string;
  ok: boolean;
}

export interface SeoPosition {
  keyword: string;
  position: number;
  clicks: number;
  impressions: number;
  trend: "up" | "down" | "stable";
}

// ────────────────────────────────────────────────────────────────────────────
// SSE Events  [REAL]
// Source: GET /api/athos-events (Next.js proxy → POST /api/events)
// ────────────────────────────────────────────────────────────────────────────

export interface SseStatusEvent extends AthosStatus {}

export interface SseSessionEvent {
  id?: string;
  ts?: string;
  type?: string;
  engine?: string;
  t?: string;
  [key: string]: unknown;
}

export interface SseHeartbeat {
  ts: number;
  server: string;
}

export interface SseErrorEvent {
  error: string;
}

// ────────────────────────────────────────────────────────────────────────────
// Performance  [MIXTE — obs REAL, Lighthouse MOCK]
// Source: /api/observability (REAL) + /api/performance (CODEX, not yet implemented)
// ────────────────────────────────────────────────────────────────────────────

export interface LighthouseResult {
  site: string;
  perf: number;
  a11y: number;
  seo: number;
  bp: number;
  mobile: number;
  nodata?: boolean;
}

export interface ApiLatencySample {
  endpoint: string;
  p50: number;
  p95: number;
  ok: boolean;
}

export interface PerformancePayload {
  lighthouse?: LighthouseResult[];
  api_latencies?: ApiLatencySample[];
  uptime_seconds?: number;
  health_score?: number;
  errors?: string[];
}

// ────────────────────────────────────────────────────────────────────────────
// CRM  [MOCK — scope Claude UI, runtime scope Codex]
// Source: /api/crm (CODEX, not yet implemented)
// ────────────────────────────────────────────────────────────────────────────

export type ClientStatus = "active" | "prospect" | "blocked" | "done";
export type AttentionLevel = "high" | "medium" | "low";

export interface CrmClient {
  id: string;
  name: string;
  status: ClientStatus;
  attention: AttentionLevel;
  project?: string;
  stack?: string;
  monthly_value?: number;
  since?: string;
  next_action?: string;
  tags?: string[];
}

export interface CrmPayload {
  clients?: CrmClient[];
  pipeline_total?: number;
  active?: number;
  urgent?: number;
  blocked?: number;
}

// ────────────────────────────────────────────────────────────────────────────
// Commandes  [MOCK → Shopify Admin API]
// Source: /api/commandes (not yet implemented)
// ────────────────────────────────────────────────────────────────────────────

export interface Order {
  id: string;
  store: string;
  customer?: string;
  amount: number;
  currency: string;
  status: "pending" | "paid" | "shipped" | "delivered" | "cancelled" | "refunded";
  created_at: string;
}

export interface CommandesPayload {
  orders?: Order[];
  summary?: { total: number; pending: number; paid: number; shipped: number; revenue: number };
}

// ────────────────────────────────────────────────────────────────────────────
// Autonomous loop  [REAL]
// Source: POST /api/autonomous_loop  (alias: /api/loop)
// Actions: status | start | stop | pause | reset | events
// ────────────────────────────────────────────────────────────────────────────

export interface LoopPolicy {
  env_enabled: boolean;
  default_tick: number;
  skill_mutation_enabled: boolean;
}

export interface LoopEvent {
  type: string;
  ts: string;
  data?: unknown;
}

export interface AutonomousLoopPayload {
  ok?: boolean;
  running: boolean;
  iterations: number;
  idle_ticks: number;
  policy: LoopPolicy;
  last_event: LoopEvent | null;
  events?: LoopEvent[];
  requires_confirmation?: boolean;
  msg?: string;
}

// ────────────────────────────────────────────────────────────────────────────
// Task queue (runtime)  [REAL]
// Source: POST /api/tasks { action: "list" | "pause" | "resume" | "retry" | "cancel" }
// Shape differs from frontend Task — uses task_id, status is backend STATUSES set
// ────────────────────────────────────────────────────────────────────────────

export type BackendTaskStatus =
  | "queued" | "running" | "paused" | "blocked"
  | "completed" | "failed" | "cancelled" | "stale";

export interface BackendTask {
  id: string;
  task_id: string;
  title: string;
  content?: string;
  source?: string;
  kind?: string;
  priority?: number;
  status: BackendTaskStatus;
  created_at: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
  blocked_reason?: string;
  retry_count?: number;
  meta?: Record<string, unknown>;
}

export interface BackendTaskSummary {
  total: number;
  active: number;
  counts: Record<string, number>;
  recent?: BackendTask[];
}

export interface TaskListPayload {
  ok: boolean;
  tasks: BackendTask[];
  summary: BackendTaskSummary;
}

// ────────────────────────────────────────────────────────────────────────────
// Performance runtime  [REAL — obs + latency · Lighthouse not configured]
// Source: POST /api/performance
// ────────────────────────────────────────────────────────────────────────────

export interface PerformanceSystem {
  uptime_seconds: number;
  listening_ports: number;
  memory_ok: boolean;
  attached_engines: number;
  loop_running: boolean;
  server_pid?: number;
}

export interface LatencySample {
  endpoint: string;
  p50: number;
  p95: number;
  ok: boolean;
  error?: string;
}

export interface PerformanceCapabilities {
  system_metrics: boolean;
  latency_sampling: boolean;
  lighthouse_configured: boolean;
}

export interface PerformanceRuntimePayload {
  ok: boolean;
  source: string;
  system: PerformanceSystem;
  api_latencies: LatencySample[];
  lighthouse: never[];
  capabilities: PerformanceCapabilities;
}

// ────────────────────────────────────────────────────────────────────────────
// CRM runtime  [REAL PARTIAL — source: athos_projects.mem]
// Source: POST /api/crm
// data_quality: "partial" always — no dedicated CRM tool connected
// ────────────────────────────────────────────────────────────────────────────

export interface CrmClientRuntime {
  id: string;
  name: string;
  status: string;
  attention: string;
  project?: string;
  monthly_value?: number | null;
  next_action?: string;
  tags?: string[];
  blocked?: boolean;
  data_quality?: string;
}

export interface CrmRuntimePayload {
  ok: boolean;
  source: string;
  data_quality: string;
  clients: CrmClientRuntime[];
  active: number;
  urgent: number;
  blocked: number;
  pipeline_total: null;
  missing_sources?: string[];
}

// ────────────────────────────────────────────────────────────────────────────
// Task UI props  [REAL — backed by /api/tasks]
// ────────────────────────────────────────────────────────────────────────────

export interface TaskCardProps {
  task: BackendTask;
  onAction?: (taskId: string, action: "cancel" | "retry" | "pause" | "resume") => Promise<void>;
}

export interface TaskQueueViewProps {
  tasks: BackendTask[];
  summary: BackendTaskSummary;
  onAction: (taskId: string, action: "cancel" | "retry" | "pause" | "resume") => Promise<void>;
}

// ────────────────────────────────────────────────────────────────────────────
// Future Codex interfaces — Session writer  [CODEX]
// ────────────────────────────────────────────────────────────────────────────

export interface SessionNote {
  note: string;
  engine?: string;
  ts?: string;
}

export interface SessionNoteResponse {
  ok: boolean;
  written?: number;
  error?: string;
}
