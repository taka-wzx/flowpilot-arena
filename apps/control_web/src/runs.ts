import { authorizedApiFetch } from "./auth";

export type DemoProcess = "joiner" | "mover" | "leaver";
export type RunStatus =
  | "waiting_approval"
  | "queued"
  | "leased"
  | "running"
  | "recovering"
  | "verifying"
  | "finished_ungraded"
  | "failed"
  | "cancelled"
  | "expired";

export type ProductionRun = Readonly<{
  runId: string;
  organizationId: string;
  taskId: string;
  process: DemoProcess;
  category: "standard_joiner" | "standard_mover" | "standard_leaver";
  approvalRequestId: string | null;
  actionType: string;
  status: RunStatus;
  version: number;
  acceptedAt: string;
  queuedAt: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  updatedAt: string;
  terminalReason: string | null;
  receiptReference: string | null;
  auditSequence: number;
}>;

export type SafeTraceEvent = Readonly<{
  sequence: number;
  phase: TracePhase;
  status: TraceStatus;
  failureCategory: FailureCategory;
  reason: TraceReason;
  observedAt: string;
}>;

export type SafeReplayStep = Readonly<{
  ordinal: number;
  phase: TracePhase;
  status: TraceStatus;
  failureCategory: FailureCategory;
  reason: TraceReason;
  observedAt: string;
}>;

export type RunTrace = Readonly<{
  run: ProductionRun;
  events: readonly SafeTraceEvent[];
  replaySteps: readonly SafeReplayStep[];
  terminalStatus: RunStatus;
  failureCategory: FailureCategory;
}>;

export class RunRequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const ORGANIZATION_ID = /^org_[A-Za-z0-9_-]{8,64}$/u;
const RUN_ID = /^run_[A-Za-z0-9_-]{8,64}$/u;
const USER_ID = /^usr_[A-Za-z0-9_-]{8,64}$/u;
const APPROVAL_ID = /^apr_[A-Za-z0-9_-]{8,64}$/u;
const GRANT_ID = /^grt_[A-Za-z0-9_-]{8,64}$/u;
const EXECUTION_ID = /^exe_[A-Za-z0-9_-]{8,64}$/u;
const OUTBOX_ID = /^out_[A-Za-z0-9_-]{8,64}$/u;
const EVENT_ID = /^obs_[A-Za-z0-9_-]{8,64}$/u;
const STEP_REFERENCE = /^[a-z][a-z0-9_]{1,39}$/u;
const ACTION = /^[a-z][a-z0-9_]{1,63}$/u;
const SHA256 = /^[0-9a-f]{64}$/u;
const TRACE_ID = /^[0-9a-f]{32}$/u;
const SPAN_ID = /^[0-9a-f]{16}$/u;
const RECEIPT_REFERENCE = /^[A-Za-z0-9_-]{8,80}$/u;
const IDEMPOTENCY_KEY = /^[A-Za-z0-9._:-]{16,80}$/u;
const UTC_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/u;

const TASK_IDS = new Set([
  "w7-jml-joiner-001-v1",
  "w7-jml-joiner-001-v2",
  "w7-jml-joiner-002-v1",
  "w7-jml-joiner-002-v2",
  "w7-jml-mover-001-v1",
  "w7-jml-mover-001-v2",
  "w7-jml-leaver-001-v1",
  "w7-jml-leaver-001-v2",
]);
const RUN_STATUSES = new Set<RunStatus>([
  "waiting_approval",
  "queued",
  "leased",
  "running",
  "recovering",
  "verifying",
  "finished_ungraded",
  "failed",
  "cancelled",
  "expired",
]);
const TERMINAL_REASONS = new Set([
  "agent_finished",
  "agent_failed",
  "authorization_invalid",
  "queue_expired",
  "lease_exhausted",
  "cancelled_by_actor",
  "workflow_rejected",
  "receipt_invalid",
  "worker_drained",
  "dependency_unavailable",
]);

const TRACE_PHASES = [
  "admission",
  "approval",
  "outbox",
  "lease",
  "dispatch",
  "workflow",
  "recovery",
  "planning",
  "browser",
  "receipt",
  "grader",
  "audit",
  "cost",
  "terminal",
  "replay",
  "dashboard",
] as const;
type TracePhase = (typeof TRACE_PHASES)[number];
const TRACE_PHASE_SET = new Set<string>(TRACE_PHASES);

const TRACE_STATUSES = [
  "accepted",
  "waiting",
  "queued",
  "leased",
  "running",
  "recovered",
  "released",
  "succeeded",
  "failed",
  "cancelled",
  "rejected",
  "pending",
  "exported",
] as const;
type TraceStatus = (typeof TRACE_STATUSES)[number];
const TRACE_STATUS_SET = new Set<string>(TRACE_STATUSES);

const FAILURE_CATEGORIES = [
  "none",
  "authn",
  "authz",
  "approval",
  "schema",
  "rate_limit",
  "backpressure",
  "queue_expiry",
  "lease_fence",
  "workflow_rejected",
  "dependency_unavailable",
  "browser_timeout",
  "browser_error",
  "planning_failure",
  "recovery_failure",
  "receipt_invalid",
  "grader_verification",
  "audit_verification",
] as const;
type FailureCategory = (typeof FAILURE_CATEGORIES)[number];
const FAILURE_CATEGORY_SET = new Set<string>(FAILURE_CATEGORIES);

const TRACE_REASONS = [
  "admitted_queued",
  "admitted_waiting_approval",
  "approval_handoff",
  "outbox_ready",
  "lease_claimed",
  "lease_recovered",
  "lease_heartbeat",
  "lease_released",
  "stale_fence_rejected",
  "worker_dispatched",
  "temporal_reference",
  "temporal_deduplicated",
  "recovery_summary",
  "planning_summary",
  "browser_step",
  "browser_summary",
  "receipt_recorded",
  "grader_pending",
  "audit_reference",
  "fake_cost_accounted",
  "run_finished_ungraded",
  "run_failed",
  "run_cancelled",
  "run_expired",
  "replay_exported",
  "dashboard_exported",
] as const;
type TraceReason = (typeof TRACE_REASONS)[number];
const TRACE_REASON_SET = new Set<string>(TRACE_REASONS);

const exactKeys = (value: Record<string, unknown>, expected: readonly string[]): boolean => {
  const actual = Object.keys(value).sort();
  const required = [...expected].sort();
  return actual.length === required.length && actual.every((item, index) => item === required[index]);
};

const record = (value: unknown, message: string): Record<string, unknown> => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(message);
  return value as Record<string, unknown>;
};

const validTimestamp = (value: unknown): value is string =>
  typeof value === "string" && UTC_TIMESTAMP.test(value) && !Number.isNaN(Date.parse(value));

const validInteger = (value: unknown, minimum: number, maximum = Number.MAX_SAFE_INTEGER): value is number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= minimum && value <= maximum;

const nullablePattern = (value: unknown, pattern: RegExp): boolean =>
  value === null || (typeof value === "string" && pattern.test(value));

const pathId = (value: string, pattern: RegExp, label: string): string => {
  if (!pattern.test(value)) throw new Error(`${label} is invalid`);
  return value;
};

const latestTimestamp = (values: readonly (string | null)[]): string => {
  const present = values.filter((value): value is string => value !== null);
  return present.reduce((latest, value) => (Date.parse(value) > Date.parse(latest) ? value : latest));
};

export const parseProductionRun = (value: unknown): ProductionRun => {
  const item = record(value, "Production run response is invalid");
  const expected = [
    "schema_version",
    "run_id",
    "organization_id",
    "requester_user_id",
    "executor_user_id",
    "task_id",
    "process",
    "category",
    "approval_request_id",
    "grant_id",
    "execution_id",
    "action_type",
    "parameter_hash",
    "authorization_hash",
    "approval_set_hash",
    "payload_hash",
    "status",
    "version",
    "workflow_hash",
    "fencing_token",
    "accepted_at",
    "queued_at",
    "started_at",
    "finished_at",
    "terminal_reason",
    "receipt_reference",
    "audit_sequence",
  ];
  const processCategories: Record<DemoProcess, ProductionRun["category"]> = {
    joiner: "standard_joiner",
    mover: "standard_mover",
    leaver: "standard_leaver",
  };
  if (
    !exactKeys(item, expected) ||
    item.schema_version !== "w12-production-run/1.0" ||
    typeof item.run_id !== "string" ||
    !RUN_ID.test(item.run_id) ||
    typeof item.organization_id !== "string" ||
    !ORGANIZATION_ID.test(item.organization_id) ||
    typeof item.requester_user_id !== "string" ||
    !USER_ID.test(item.requester_user_id) ||
    typeof item.executor_user_id !== "string" ||
    !USER_ID.test(item.executor_user_id) ||
    typeof item.task_id !== "string" ||
    !TASK_IDS.has(item.task_id) ||
    (item.process !== "joiner" && item.process !== "mover" && item.process !== "leaver") ||
    item.category !== processCategories[item.process] ||
    !nullablePattern(item.approval_request_id, APPROVAL_ID) ||
    !nullablePattern(item.grant_id, GRANT_ID) ||
    !nullablePattern(item.execution_id, EXECUTION_ID) ||
    typeof item.action_type !== "string" ||
    !ACTION.test(item.action_type) ||
    typeof item.parameter_hash !== "string" ||
    !SHA256.test(item.parameter_hash) ||
    typeof item.authorization_hash !== "string" ||
    !SHA256.test(item.authorization_hash) ||
    !nullablePattern(item.approval_set_hash, SHA256) ||
    typeof item.payload_hash !== "string" ||
    !SHA256.test(item.payload_hash) ||
    typeof item.status !== "string" ||
    !RUN_STATUSES.has(item.status as RunStatus) ||
    !validInteger(item.version, 1) ||
    typeof item.workflow_hash !== "string" ||
    !SHA256.test(item.workflow_hash) ||
    !validInteger(item.fencing_token, 0) ||
    !validTimestamp(item.accepted_at) ||
    (item.queued_at !== null && !validTimestamp(item.queued_at)) ||
    (item.started_at !== null && !validTimestamp(item.started_at)) ||
    (item.finished_at !== null && !validTimestamp(item.finished_at)) ||
    (item.terminal_reason !== null &&
      (typeof item.terminal_reason !== "string" || !TERMINAL_REASONS.has(item.terminal_reason))) ||
    !nullablePattern(item.receipt_reference, RECEIPT_REFERENCE) ||
    !validInteger(item.audit_sequence, 1)
  ) {
    throw new Error("Production run response is invalid");
  }
  const status = item.status as RunStatus;
  const terminal = isTerminalRun(status);
  if ((terminal && item.finished_at === null) || (!terminal && item.terminal_reason !== null)) {
    throw new Error("Production run terminal state is invalid");
  }
  const queuedAt = item.queued_at as string | null;
  const startedAt = item.started_at as string | null;
  const finishedAt = item.finished_at as string | null;
  return {
    runId: item.run_id,
    organizationId: item.organization_id,
    taskId: item.task_id,
    process: item.process,
    category: item.category as ProductionRun["category"],
    approvalRequestId: item.approval_request_id as string | null,
    actionType: item.action_type,
    status,
    version: item.version,
    acceptedAt: item.accepted_at,
    queuedAt,
    startedAt,
    finishedAt,
    updatedAt: latestTimestamp([item.accepted_at, queuedAt, startedAt, finishedAt]),
    terminalReason: item.terminal_reason as string | null,
    receiptReference: item.receipt_reference as string | null,
    auditSequence: item.audit_sequence,
  };
};

const parseTraceAttributes = (value: unknown): void => {
  const item = record(value, "Trace attributes are invalid");
  const expected = [
    "schema_version", "run_status", "approval_request_id", "grant_id", "execution_id",
    "authorization_hash", "approval_set_hash", "outbox_id", "outbox_status", "lease_status",
    "workflow_hash", "worker_reference", "receipt_reference", "checkpoint_hash", "audit_sequence",
    "version", "fencing_token", "lease_version", "attempt_count", "count", "event_count",
    "step_count", "checkpoint_count", "activity_attempts", "retries", "session_recoveries",
    "replans", "route_decisions", "dom_observations", "images", "duration_ms", "latency_ms",
    "model_calls", "input_tokens", "output_tokens", "fake_cost_microusd", "real_cost_microusd",
    "step_id", "completed_step_ids", "sensitive_fields_present",
  ];
  const nullableInteger = (candidate: unknown, minimum: number, maximum: number) =>
    candidate === null || validInteger(candidate, minimum, maximum);
  if (
    !exactKeys(item, expected) ||
    item.schema_version !== "w13-trace-attributes/1.0" ||
    (item.run_status !== null &&
      (typeof item.run_status !== "string" || !RUN_STATUSES.has(item.run_status as RunStatus))) ||
    !nullablePattern(item.approval_request_id, APPROVAL_ID) ||
    !nullablePattern(item.grant_id, GRANT_ID) ||
    !nullablePattern(item.execution_id, EXECUTION_ID) ||
    !nullablePattern(item.authorization_hash, SHA256) ||
    !nullablePattern(item.approval_set_hash, SHA256) ||
    !nullablePattern(item.outbox_id, OUTBOX_ID) ||
    (item.outbox_status !== null &&
      !new Set(["ready", "leased", "dispatched", "closed", "cancelled", "expired", "failed"]).has(item.outbox_status as string)) ||
    (item.lease_status !== null &&
      !new Set(["active", "released", "expired", "completed", "failed"]).has(item.lease_status as string)) ||
    !nullablePattern(item.workflow_hash, SHA256) ||
    !nullablePattern(item.worker_reference, SHA256) ||
    !nullablePattern(item.receipt_reference, RECEIPT_REFERENCE) ||
    !nullablePattern(item.checkpoint_hash, SHA256) ||
    !nullableInteger(item.audit_sequence, 1, Number.MAX_SAFE_INTEGER) ||
    !nullableInteger(item.version, 1, Number.MAX_SAFE_INTEGER) ||
    !nullableInteger(item.fencing_token, 0, Number.MAX_SAFE_INTEGER) ||
    !nullableInteger(item.lease_version, 0, Number.MAX_SAFE_INTEGER) ||
    !nullableInteger(item.attempt_count, 0, 3) ||
    !nullableInteger(item.count, 0, 1_000_000) ||
    !nullableInteger(item.event_count, 0, 1_000_000) ||
    !nullableInteger(item.step_count, 0, 64) ||
    !nullableInteger(item.checkpoint_count, 0, 64) ||
    !nullableInteger(item.activity_attempts, 0, 64) ||
    !nullableInteger(item.retries, 0, 64) ||
    !nullableInteger(item.session_recoveries, 0, 8) ||
    !nullableInteger(item.replans, 0, 8) ||
    !nullableInteger(item.route_decisions, 0, 1_000_000) ||
    !nullableInteger(item.dom_observations, 0, 1_000_000) ||
    !nullableInteger(item.images, 0, 1_000_000) ||
    !nullableInteger(item.duration_ms, 0, 3_600_000) ||
    !nullableInteger(item.latency_ms, 0, 3_600_000) ||
    !nullableInteger(item.model_calls, 0, 1_000_000) ||
    !nullableInteger(item.input_tokens, 0, 1_000_000_000) ||
    !nullableInteger(item.output_tokens, 0, 1_000_000_000) ||
    !nullableInteger(item.fake_cost_microusd, 0, 1_000_000_000) ||
    (item.real_cost_microusd !== null && item.real_cost_microusd !== 0) ||
    !nullablePattern(item.step_id, STEP_REFERENCE) ||
    !Array.isArray(item.completed_step_ids) ||
    item.completed_step_ids.length > 16 ||
    !item.completed_step_ids.every((step) => typeof step === "string" && STEP_REFERENCE.test(step)) ||
    item.sensitive_fields_present !== false
  ) {
    throw new Error("Trace attributes are invalid");
  }
};

const parseTraceEvent = (
  value: unknown,
  organizationId: string,
  runId: string,
  traceId: string,
): SafeTraceEvent => {
  const item = record(value, "Trace event is invalid");
  if (
    !exactKeys(item, [
      "schema_version", "event_id", "organization_id", "run_id", "event_sequence", "trace_id",
      "span_id", "parent_span_id", "phase", "status", "failure_category", "reason", "attributes",
      "attributes_hash", "event_hash", "observed_at",
    ]) ||
    item.schema_version !== "w13-observability-event/1.0" ||
    typeof item.event_id !== "string" || !EVENT_ID.test(item.event_id) ||
    item.organization_id !== organizationId || item.run_id !== runId ||
    !validInteger(item.event_sequence, 1, 256) ||
    item.trace_id !== traceId ||
    typeof item.span_id !== "string" || !SPAN_ID.test(item.span_id) ||
    !nullablePattern(item.parent_span_id, SPAN_ID) ||
    typeof item.phase !== "string" || !TRACE_PHASE_SET.has(item.phase) ||
    typeof item.status !== "string" || !TRACE_STATUS_SET.has(item.status) ||
    typeof item.failure_category !== "string" || !FAILURE_CATEGORY_SET.has(item.failure_category) ||
    typeof item.reason !== "string" || !TRACE_REASON_SET.has(item.reason) ||
    typeof item.attributes_hash !== "string" || !SHA256.test(item.attributes_hash) ||
    typeof item.event_hash !== "string" || !SHA256.test(item.event_hash) ||
    !validTimestamp(item.observed_at)
  ) {
    throw new Error("Trace event is invalid");
  }
  parseTraceAttributes(item.attributes);
  return {
    sequence: item.event_sequence,
    phase: item.phase as TracePhase,
    status: item.status as TraceStatus,
    failureCategory: item.failure_category as FailureCategory,
    reason: item.reason as TraceReason,
    observedAt: item.observed_at,
  };
};

const parseReplayStep = (value: unknown): SafeReplayStep => {
  const item = record(value, "Replay step is invalid");
  if (
    !exactKeys(item, [
      "schema_version", "ordinal", "phase", "status", "failure_category", "reason",
      "reference_hash", "observed_at",
    ]) ||
    item.schema_version !== "w13-replay-step/1.0" ||
    !validInteger(item.ordinal, 1, 256) ||
    typeof item.phase !== "string" || !TRACE_PHASE_SET.has(item.phase) ||
    typeof item.status !== "string" || !TRACE_STATUS_SET.has(item.status) ||
    typeof item.failure_category !== "string" || !FAILURE_CATEGORY_SET.has(item.failure_category) ||
    typeof item.reason !== "string" || !TRACE_REASON_SET.has(item.reason) ||
    typeof item.reference_hash !== "string" || !SHA256.test(item.reference_hash) ||
    !validTimestamp(item.observed_at)
  ) {
    throw new Error("Replay step is invalid");
  }
  return {
    ordinal: item.ordinal,
    phase: item.phase as TracePhase,
    status: item.status as TraceStatus,
    failureCategory: item.failure_category as FailureCategory,
    reason: item.reason as TraceReason,
    observedAt: item.observed_at,
  };
};

export const parseRunTrace = (value: unknown): RunTrace => {
  const item = record(value, "Run trace response is invalid");
  if (
    !exactKeys(item, ["schema_version", "run", "trace_id", "events", "replay_steps", "cost", "dashboard", "export_hash"]) ||
    item.schema_version !== "w13-run-trace-export/1.0" ||
    typeof item.trace_id !== "string" || !TRACE_ID.test(item.trace_id) ||
    !Array.isArray(item.events) || item.events.length > 256 ||
    !Array.isArray(item.replay_steps) || item.replay_steps.length > 256 ||
    typeof item.export_hash !== "string" || !SHA256.test(item.export_hash)
  ) {
    throw new Error("Run trace response is invalid");
  }
  const run = parseProductionRun(item.run);
  let previousSpanId: string | null = null;
  const events = item.events.map((event, index) => {
    const raw = record(event, "Trace event is invalid");
    if ((index === 0 && raw.parent_span_id !== null) ||
      (index > 0 && raw.parent_span_id !== previousSpanId)) {
      throw new Error("Run trace parent chain is invalid");
    }
    const parsed = parseTraceEvent(event, run.organizationId, run.runId, item.trace_id as string);
    previousSpanId = raw.span_id as string;
    return parsed;
  });
  const replaySteps = item.replay_steps.map(parseReplayStep);
  if (
    events.some((event, index) => event.sequence !== index + 1) ||
    replaySteps.some((step, index) => step.ordinal !== index + 1)
  ) {
    throw new Error("Run trace ordering is invalid");
  }
  const cost = record(item.cost, "Trace cost summary is invalid");
  if (
    !exactKeys(cost, ["schema_version", "model_calls", "input_tokens", "output_tokens", "fake_cost_microusd", "real_cost_microusd"]) ||
    cost.schema_version !== "w13-cost-summary/1.0" ||
    !validInteger(cost.model_calls, 0, 1_000_000) ||
    !validInteger(cost.input_tokens, 0, 1_000_000_000) ||
    !validInteger(cost.output_tokens, 0, 1_000_000_000) ||
    !validInteger(cost.fake_cost_microusd, 0, 1_000_000_000) ||
    cost.real_cost_microusd !== 0
  ) {
    throw new Error("Trace cost summary is invalid");
  }
  const dashboard = record(item.dashboard, "Trace dashboard is invalid");
  if (
    !exactKeys(dashboard, [
      "schema_version", "event_count", "replay_step_count", "terminal_status", "failure_category",
      "model_calls", "fake_cost_microusd", "real_cost_microusd", "sensitive_fields_present", "dashboard_hash",
    ]) ||
    dashboard.schema_version !== "w13-trace-dashboard/1.0" ||
    dashboard.event_count !== events.length || dashboard.replay_step_count !== replaySteps.length ||
    typeof dashboard.terminal_status !== "string" || !RUN_STATUSES.has(dashboard.terminal_status as RunStatus) ||
    dashboard.terminal_status !== run.status ||
    typeof dashboard.failure_category !== "string" || !FAILURE_CATEGORY_SET.has(dashboard.failure_category) ||
    !validInteger(dashboard.model_calls, 0, 1_000_000) ||
    !validInteger(dashboard.fake_cost_microusd, 0, 1_000_000_000) ||
    dashboard.real_cost_microusd !== 0 || dashboard.sensitive_fields_present !== false ||
    typeof dashboard.dashboard_hash !== "string" || !SHA256.test(dashboard.dashboard_hash)
  ) {
    throw new Error("Trace dashboard is invalid");
  }
  return {
    run,
    events,
    replaySteps,
    terminalStatus: dashboard.terminal_status as RunStatus,
    failureCategory: dashboard.failure_category as FailureCategory,
  };
};

const requireOk = (response: Response, message: string): void => {
  if (!response.ok) throw new RunRequestError(message, response.status);
};

export const loadProductionRuns = async (organizationId: string): Promise<readonly ProductionRun[]> => {
  const organization = pathId(organizationId, ORGANIZATION_ID, "Organization ID");
  const response = await authorizedApiFetch(`/api/v1/organizations/${organization}/production-runs`);
  requireOk(response, "Production run list request failed");
  const value = record(await response.json(), "Production run list is invalid");
  if (
    !exactKeys(value, ["schema_version", "items", "count"]) ||
    value.schema_version !== "w12-production-run-list/1.0" ||
    !Array.isArray(value.items) || value.items.length > 100 || value.count !== value.items.length
  ) {
    throw new Error("Production run list is invalid");
  }
  const items = value.items.map(parseProductionRun);
  if (items.some((run) => run.organizationId !== organizationId)) {
    throw new Error("Production run organization is invalid");
  }
  return items;
};

export const loadProductionRun = async (organizationId: string, runId: string): Promise<ProductionRun> => {
  const organization = pathId(organizationId, ORGANIZATION_ID, "Organization ID");
  const run = pathId(runId, RUN_ID, "Run ID");
  const response = await authorizedApiFetch(`/api/v1/organizations/${organization}/production-runs/${run}`);
  requireOk(response, "Production run detail request failed");
  const parsed = parseProductionRun(await response.json());
  if (parsed.organizationId !== organizationId || parsed.runId !== runId) {
    throw new Error("Production run identity is invalid");
  }
  return parsed;
};

export const loadProductionRunTrace = async (organizationId: string, runId: string): Promise<RunTrace> => {
  const organization = pathId(organizationId, ORGANIZATION_ID, "Organization ID");
  const run = pathId(runId, RUN_ID, "Run ID");
  const response = await authorizedApiFetch(`/api/v1/organizations/${organization}/production-runs/${run}/trace`);
  requireOk(response, "Production run trace request failed");
  const parsed = parseRunTrace(await response.json());
  if (parsed.run.organizationId !== organizationId || parsed.run.runId !== runId) {
    throw new Error("Production run trace identity is invalid");
  }
  return parsed;
};

const DEMO_TASKS: Record<DemoProcess, Readonly<{ taskId: string; category: ProductionRun["category"] }>> = {
  joiner: { taskId: "w7-jml-joiner-001-v1", category: "standard_joiner" },
  mover: { taskId: "w7-jml-mover-001-v1", category: "standard_mover" },
  leaver: { taskId: "w7-jml-leaver-001-v1", category: "standard_leaver" },
};

export const createDemoIdempotencyKey = (
  process: DemoProcess,
  cryptoProvider: Crypto = window.crypto,
): string => {
  const bytes = new Uint8Array(12);
  cryptoProvider.getRandomValues(bytes);
  const suffix = [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  return `w17-demo-${process}-${suffix}`;
};

export const submitDemoRun = async (
  organizationId: string,
  process: DemoProcess,
  idempotencyKey: string,
): Promise<ProductionRun> => {
  const organization = pathId(organizationId, ORGANIZATION_ID, "Organization ID");
  if (!IDEMPOTENCY_KEY.test(idempotencyKey)) throw new Error("Idempotency key is invalid");
  const task = DEMO_TASKS[process];
  const response = await authorizedApiFetch(`/api/v1/organizations/${organization}/production-runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({
      schema_version: "w12-production-run-create/1.0",
      task_id: task.taskId,
      process,
      category: task.category,
      action_type: "generate_plan",
      parameters: {
        schema_version: "w11-task-parameters/1.0",
        task_reference: task.taskId,
      },
    }),
  });
  requireOk(response, "Synthetic run submission failed");
  const parsed = parseProductionRun(await response.json());
  if (parsed.organizationId !== organizationId || parsed.process !== process || parsed.taskId !== task.taskId) {
    throw new Error("Synthetic run response is invalid");
  }
  return parsed;
};

export const isTerminalRun = (status: RunStatus): boolean =>
  status === "finished_ungraded" || status === "failed" || status === "cancelled" || status === "expired";

export const RUN_POLL_INTERVAL_MS = 5_000;
export const RUN_POLL_MAX_DURATION_MS = 2 * 60_000;

type PollingOptions = Readonly<{
  organizationId: string;
  initialRun: ProductionRun;
  onUpdate: (run: ProductionRun) => void;
  onError: (error: unknown) => void;
  onTimeout: () => void;
  loader?: typeof loadProductionRun;
  documentRef?: Document;
  intervalMs?: number;
  maxDurationMs?: number;
  now?: () => number;
}>;

export const startRunPolling = (options: PollingOptions): (() => void) => {
  if (isTerminalRun(options.initialRun.status)) return () => undefined;
  const loader = options.loader ?? loadProductionRun;
  const documentRef = options.documentRef ?? document;
  const intervalMs = options.intervalMs ?? RUN_POLL_INTERVAL_MS;
  const maxDurationMs = options.maxDurationMs ?? RUN_POLL_MAX_DURATION_MS;
  const now = options.now ?? Date.now;
  const startedAt = now();
  let active = true;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const stop = () => {
    if (!active) return;
    active = false;
    if (timer !== null) clearTimeout(timer);
    documentRef.removeEventListener("visibilitychange", visibilityChanged);
  };

  const schedule = () => {
    if (active) timer = setTimeout(() => void tick(), intervalMs);
  };

  const tick = async () => {
    if (!active) return;
    if (documentRef.visibilityState === "hidden") {
      stop();
      return;
    }
    if (now() - startedAt >= maxDurationMs) {
      stop();
      options.onTimeout();
      return;
    }
    try {
      const run = await loader(options.organizationId, options.initialRun.runId);
      if (!active) return;
      options.onUpdate(run);
      if (isTerminalRun(run.status)) stop();
      else schedule();
    } catch (error) {
      if (!active) return;
      stop();
      options.onError(error);
    }
  };

  function visibilityChanged() {
    if (documentRef.visibilityState === "hidden") stop();
  }

  documentRef.addEventListener("visibilitychange", visibilityChanged);
  schedule();
  return stop;
};
