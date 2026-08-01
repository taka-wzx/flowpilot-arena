import { authorizedApiFetch } from "./auth";

export type ApprovalRole = "manager" | "security";
export type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "cancelled"
  | "expired"
  | "invalidated"
  | "claimed"
  | "consumed"
  | "failed";

export type ApprovalRequest = Readonly<{
  requestId: string;
  organizationId: string;
  taskId: string;
  stepId: string;
  actionType: string;
  parameterHash: string;
  riskLevel: "L2" | "L3";
  requiredRoles: readonly ApprovalRole[];
  status: ApprovalStatus;
  version: number;
  expiresAt: string;
}>;

export type AuditEvent = Readonly<{
  eventId: string;
  sequence: number;
  eventType: string;
  eventHash: string;
}>;

export type AuditSnapshot = Readonly<{
  events: readonly AuditEvent[];
  headSequence: number;
  headHash: string;
}>;

export class StaleApprovalError extends Error {}

const APPROVAL_ACTIONS = new Set([
  "create_ticket",
  "create_account",
  "assign_asset",
  "create_mailbox",
  "transfer_employee",
  "close_ticket",
  "release_asset",
  "grant_admin_privilege",
  "revoke_account",
  "disable_employee",
  "disable_mailbox",
  "transfer_file_ownership",
]);
const AUDIT_EVENT_TYPES = new Set([
  "risk_classified",
  "l4_denied",
  "approval_requested",
  "approval_approved",
  "approval_rejected",
  "request_cancelled",
  "request_expired",
  "request_invalidated",
  "grant_issued",
  "grant_claimed",
  "grant_consumed",
  "grant_rejected",
  "execution_started",
  "execution_succeeded",
  "execution_failed",
  "recovery_resumed",
  "authority_disabled",
  "audit_verified",
]);
const CLOSED_REASONS = new Set([
  "policy_rejected",
  "requester_cancelled",
  "parameters_changed",
  "authority_inactive",
  "request_expired",
]);
const UTC_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/u;

const exactKeys = (value: Record<string, unknown>, expected: readonly string[]): boolean => {
  const actual = Object.keys(value).sort();
  const required = [...expected].sort();
  return actual.length === required.length && actual.every((item, index) => item === required[index]);
};

const record = (value: unknown, message: string): Record<string, unknown> => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(message);
  }
  return value as Record<string, unknown>;
};

const closedPathId = (value: string, pattern: RegExp): string => {
  if (!pattern.test(value)) throw new Error("Approval path identifier is invalid");
  return value;
};

const organizationPath = (organizationId: string): string =>
  closedPathId(organizationId, /^org_[A-Za-z0-9_-]{8,64}$/u);

const requestPath = (requestId: string): string =>
  closedPathId(requestId, /^apr_[A-Za-z0-9_-]{8,64}$/u);

const parseRequest = (value: unknown): ApprovalRequest => {
  const item = record(value, "Approval request response is invalid");
  const expected = [
    "schema_version",
    "request_id",
    "organization_id",
    "task_id",
    "step_id",
    "action_type",
    "parameter_hash",
    "risk_level",
    "requester_user_id",
    "executor_user_id",
    "required_roles",
    "status",
    "version",
    "expires_at",
    "closed_reason",
    "audit_sequence",
    "created_at",
    "updated_at",
  ];
  const statuses = new Set<ApprovalStatus>([
    "pending",
    "approved",
    "rejected",
    "cancelled",
    "expired",
    "invalidated",
    "claimed",
    "consumed",
    "failed",
  ]);
  const roles = item.required_roles;
  const riskRoles =
    item.risk_level === "L2" ? ["manager"] : ["manager", "security"];
  if (
    !exactKeys(item, expected) ||
    item.schema_version !== "w11-approval-request/1.0" ||
    typeof item.request_id !== "string" ||
    !/^apr_[A-Za-z0-9_-]{8,64}$/u.test(item.request_id) ||
    typeof item.organization_id !== "string" ||
    !/^org_[A-Za-z0-9_-]{8,64}$/u.test(item.organization_id) ||
    typeof item.task_id !== "string" ||
    !/^[A-Za-z][A-Za-z0-9_-]{7,79}$/u.test(item.task_id) ||
    typeof item.step_id !== "string" ||
    !/^[a-z][a-z0-9_]{1,39}$/u.test(item.step_id) ||
    typeof item.action_type !== "string" ||
    !APPROVAL_ACTIONS.has(item.action_type) ||
    typeof item.parameter_hash !== "string" ||
    !/^[0-9a-f]{64}$/u.test(item.parameter_hash) ||
    (item.risk_level !== "L2" && item.risk_level !== "L3") ||
    !Array.isArray(roles) ||
    !roles.every((role) => role === "manager" || role === "security") ||
    roles.length !== riskRoles.length ||
    !roles.every((role, index) => role === riskRoles[index]) ||
    typeof item.requester_user_id !== "string" ||
    !/^usr_[A-Za-z0-9_-]{8,64}$/u.test(item.requester_user_id) ||
    typeof item.executor_user_id !== "string" ||
    !/^usr_[A-Za-z0-9_-]{8,64}$/u.test(item.executor_user_id) ||
    typeof item.status !== "string" ||
    !statuses.has(item.status as ApprovalStatus) ||
    typeof item.version !== "number" ||
    !Number.isSafeInteger(item.version) ||
    item.version < 1 ||
    typeof item.expires_at !== "string" ||
    !UTC_TIMESTAMP.test(item.expires_at) ||
    (item.closed_reason !== null &&
      (typeof item.closed_reason !== "string" || !CLOSED_REASONS.has(item.closed_reason))) ||
    typeof item.audit_sequence !== "number" ||
    !Number.isSafeInteger(item.audit_sequence) ||
    item.audit_sequence < 1 ||
    typeof item.created_at !== "string" ||
    !UTC_TIMESTAMP.test(item.created_at) ||
    typeof item.updated_at !== "string" ||
    !UTC_TIMESTAMP.test(item.updated_at)
  ) {
    throw new Error("Approval request response is invalid");
  }
  return {
    requestId: item.request_id,
    organizationId: item.organization_id,
    taskId: item.task_id,
    stepId: item.step_id,
    actionType: item.action_type,
    parameterHash: item.parameter_hash,
    riskLevel: item.risk_level,
    requiredRoles: roles as ApprovalRole[],
    status: item.status as ApprovalStatus,
    version: item.version,
    expiresAt: item.expires_at,
  };
};

export const loadCurrentApprovalRoles = async (): Promise<readonly ApprovalRole[]> => {
  const response = await authorizedApiFetch("/api/v1/approval-authorities/me");
  if (!response.ok) throw new Error("Current approval authorities request failed");
  const value = record(await response.json(), "Current approval authorities response is invalid");
  if (
    !exactKeys(value, ["schema_version", "roles", "authority_ids", "authorization_hash"]) ||
    value.schema_version !== "w11-current-approval-authorities/1.0" ||
    !Array.isArray(value.roles) ||
    !value.roles.every((role) => role === "manager" || role === "security") ||
    !Array.isArray(value.authority_ids) ||
    value.authority_ids.length !== value.roles.length ||
    !value.authority_ids.every(
      (authority) =>
        typeof authority === "string" && /^aut_[A-Za-z0-9_-]{8,64}$/u.test(authority),
    ) ||
    typeof value.authorization_hash !== "string" ||
    !/^[0-9a-f]{64}$/u.test(value.authorization_hash)
  ) {
    throw new Error("Current approval authorities response is invalid");
  }
  return value.roles as ApprovalRole[];
};

export const loadApprovalRequests = async (
  organizationId: string,
): Promise<readonly ApprovalRequest[]> => {
  const organization = organizationPath(organizationId);
  const response = await authorizedApiFetch(
    `/api/v1/organizations/${organization}/approval-requests`,
  );
  if (!response.ok) throw new Error("Approval request list failed");
  const value = record(await response.json(), "Approval request list is invalid");
  if (
    !exactKeys(value, ["schema_version", "items", "count"]) ||
    value.schema_version !== "w11-approval-request-list/1.0" ||
    !Array.isArray(value.items) ||
    value.count !== value.items.length
  ) {
    throw new Error("Approval request list is invalid");
  }
  const items = value.items.map(parseRequest);
  if (items.some((item) => item.organizationId !== organizationId)) {
    throw new Error("Approval request organization is invalid");
  }
  return items;
};

export const loadApprovalRequest = async (
  organizationId: string,
  requestId: string,
): Promise<Readonly<{ request: ApprovalRequest; etag: string }>> => {
  const organization = organizationPath(organizationId);
  const request = requestPath(requestId);
  const response = await authorizedApiFetch(
    `/api/v1/organizations/${organization}/approval-requests/${request}`,
  );
  if (!response.ok) throw new Error("Approval request detail failed");
  const etag = response.headers.get("ETag");
  if (etag === null || !/^"w11-approval-request-[0-9a-f]{24}-v[1-9][0-9]*"$/u.test(etag)) {
    throw new Error("Approval request ETag is invalid");
  }
  const parsed = parseRequest(await response.json());
  if (parsed.organizationId !== organizationId || parsed.requestId !== requestId) {
    throw new Error("Approval request identity is invalid");
  }
  return { request: parsed, etag };
};

export const decideApprovalRequest = async (
  organizationId: string,
  requestId: string,
  etag: string,
  decision: "approved" | "rejected",
): Promise<ApprovalRequest> => {
  const organization = organizationPath(organizationId);
  const request = requestPath(requestId);
  if (!/^"w11-approval-request-[0-9a-f]{24}-v[1-9][0-9]*"$/u.test(etag)) {
    throw new Error("Approval request ETag is invalid");
  }
  const response = await authorizedApiFetch(
    `/api/v1/organizations/${organization}/approval-requests/${request}/decisions`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "If-Match": etag },
      body: JSON.stringify({
        schema_version: "w11-approval-decision-create/1.0",
        decision,
        reason: decision === "approved" ? "policy_satisfied" : "policy_rejected",
      }),
    },
  );
  if (response.status === 412 || response.status === 428) {
    throw new StaleApprovalError("Approval request changed; reload before deciding");
  }
  if (!response.ok) throw new Error("Approval decision failed");
  const value = record(await response.json(), "Approval decision response is invalid");
  if (
    !exactKeys(value, ["schema_version", "decision", "request", "grant_issued"]) ||
    value.schema_version !== "w11-approval-decision-result/1.0" ||
    typeof value.grant_issued !== "boolean"
  ) {
    throw new Error("Approval decision response is invalid");
  }
  const serialized = JSON.stringify(value).toLowerCase();
  if (serialized.includes("credential") || serialized.includes("nonce") || serialized.includes("token")) {
    throw new Error("Approval response exposed prohibited grant material");
  }
  return parseRequest(value.request);
};

export const loadAuditEvents = async (organizationId: string): Promise<AuditSnapshot> => {
  const organization = organizationPath(organizationId);
  const response = await authorizedApiFetch(
    `/api/v1/organizations/${organization}/audit-events`,
  );
  if (!response.ok) throw new Error("Audit event list failed");
  const value = record(await response.json(), "Audit event list is invalid");
  if (
    !exactKeys(value, ["schema_version", "items", "count", "head_sequence", "head_hash"]) ||
    value.schema_version !== "w11-audit-event-list/1.0" ||
    !Array.isArray(value.items) ||
    value.count !== value.items.length ||
    typeof value.head_sequence !== "number" ||
    !Number.isSafeInteger(value.head_sequence) ||
    value.head_sequence < 0 ||
    typeof value.head_hash !== "string" ||
    !/^[0-9a-f]{64}$/u.test(value.head_hash)
  ) {
    throw new Error("Audit event list is invalid");
  }
  const events = value.items.map((entry) => {
    const item = record(entry, "Audit event is invalid");
    if (
      !exactKeys(item, [
        "schema_version",
        "event_id",
        "organization_id",
        "sequence",
        "event_type",
        "previous_hash",
        "event_hash",
        "payload_hash",
        "created_at",
      ]) ||
      item.schema_version !== "w11-audit-event/1.0" ||
      typeof item.event_id !== "string" ||
      !/^aud_[A-Za-z0-9_-]{8,64}$/u.test(item.event_id) ||
      item.organization_id !== organizationId ||
      typeof item.sequence !== "number" ||
      !Number.isSafeInteger(item.sequence) ||
      item.sequence < 1 ||
      typeof item.event_type !== "string" ||
      !AUDIT_EVENT_TYPES.has(item.event_type) ||
      typeof item.previous_hash !== "string" ||
      !/^[0-9a-f]{64}$/u.test(item.previous_hash) ||
      typeof item.event_hash !== "string" ||
      !/^[0-9a-f]{64}$/u.test(item.event_hash) ||
      typeof item.payload_hash !== "string" ||
      !/^[0-9a-f]{64}$/u.test(item.payload_hash) ||
      typeof item.created_at !== "string" ||
      !UTC_TIMESTAMP.test(item.created_at)
    ) {
      throw new Error("Audit event is invalid");
    }
    return {
      eventId: item.event_id,
      sequence: item.sequence,
      eventType: item.event_type,
      eventHash: item.event_hash,
    };
  });
  return {
    events,
    headSequence: value.head_sequence,
    headHash: value.head_hash,
  };
};

export const verifyAuditChain = async (organizationId: string): Promise<boolean> => {
  const organization = organizationPath(organizationId);
  const response = await authorizedApiFetch(
    `/api/v1/organizations/${organization}/audit-events/verify`,
    { method: "POST" },
  );
  if (!response.ok) throw new Error("Audit verification failed");
  const value = record(await response.json(), "Audit verification response is invalid");
  if (
    !exactKeys(value, [
      "schema_version",
      "valid",
      "event_count",
      "head_sequence",
      "head_hash",
      "reason",
    ]) ||
    value.schema_version !== "w11-audit-verification/1.0" ||
    typeof value.valid !== "boolean" ||
    typeof value.event_count !== "number" ||
    !Number.isSafeInteger(value.event_count) ||
    value.event_count < 0 ||
    typeof value.head_sequence !== "number" ||
    !Number.isSafeInteger(value.head_sequence) ||
    value.head_sequence < 0 ||
    typeof value.head_hash !== "string" ||
    !/^[0-9a-f]{64}$/u.test(value.head_hash) ||
    typeof value.reason !== "string" ||
    !new Set([
      "valid",
      "sequence_mismatch",
      "previous_hash_mismatch",
      "event_hash_mismatch",
      "head_mismatch",
    ]).has(value.reason)
  ) {
    throw new Error("Audit verification response is invalid");
  }
  return value.valid;
};
