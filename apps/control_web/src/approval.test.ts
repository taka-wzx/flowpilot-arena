import { beforeEach, describe, expect, it, vi } from "vitest";

import { authorizedApiFetch } from "./auth";
import {
  StaleApprovalError,
  decideApprovalRequest,
  loadApprovalRequest,
  loadApprovalRequests,
  loadAuditEvents,
  loadCurrentApprovalRoles,
  verifyAuditChain,
} from "./approval";

vi.mock("./auth", () => ({ authorizedApiFetch: vi.fn() }));

const fetchMock = vi.mocked(authorizedApiFetch);
const organizationId = "org_syn_alpha_0001";
const requestId = "apr_syn_alpha_request_0001";

const requestPayload = {
  schema_version: "w11-approval-request/1.0",
  request_id: requestId,
  organization_id: organizationId,
  task_id: "task_syn_alpha_0001",
  step_id: "assign_asset",
  action_type: "assign_asset",
  parameter_hash: "a".repeat(64),
  risk_level: "L2",
  requester_user_id: "usr_syn_alpha_operator_0001",
  executor_user_id: "usr_syn_alpha_operator_0001",
  required_roles: ["manager"],
  status: "pending",
  version: 1,
  expires_at: "2026-07-29T12:10:00Z",
  closed_reason: null,
  audit_sequence: 2,
  created_at: "2026-07-29T12:00:00Z",
  updated_at: "2026-07-29T12:00:00Z",
};

describe("W11 approval client", () => {
  beforeEach(() => fetchMock.mockReset());

  it("loads only closed current roles and request metadata with a strong ETag", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema_version: "w11-current-approval-authorities/1.0",
            roles: ["manager"],
            authority_ids: ["aut_syn_alpha_manager_0001"],
            authorization_hash: "b".repeat(64),
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema_version: "w11-approval-request-list/1.0",
            items: [requestPayload],
            count: 1,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(requestPayload), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            ETag: '"w11-approval-request-aaaaaaaaaaaaaaaaaaaaaaaa-v1"',
          },
        }),
      );

    expect(await loadCurrentApprovalRoles()).toEqual(["manager"]);
    expect((await loadApprovalRequests(organizationId))[0]?.status).toBe("pending");
    const detail = await loadApprovalRequest(organizationId, requestId);
    expect(detail.request.parameterHash).toBe("a".repeat(64));
    expect(detail.etag).toContain("w11-approval-request");
  });

  it("sends one ETag-bound decision and rejects stale UI state", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema_version: "w11-approval-decision-result/1.0",
            decision: {
              schema_version: "w11-approval-decision/1.0",
              decision_id: "dec_syn_alpha_decision_0001",
            },
            request: { ...requestPayload, status: "approved", version: 2 },
            grant_issued: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ code: "precondition_failed" }), {
          status: 412,
          headers: { "Content-Type": "application/json" },
        }),
      );
    const etag = '"w11-approval-request-aaaaaaaaaaaaaaaaaaaaaaaa-v1"';

    const approved = await decideApprovalRequest(organizationId, requestId, etag, "approved");
    expect(approved.status).toBe("approved");
    const init = fetchMock.mock.calls[0]?.[1];
    expect((init?.headers as Record<string, string>)["If-Match"]).toBe(etag);
    expect(String(init?.body)).not.toMatch(/credential|nonce|token/iu);
    await expect(
      decideApprovalRequest(organizationId, requestId, etag, "approved"),
    ).rejects.toBeInstanceOf(StaleApprovalError);
  });

  it("loads read-only audit metadata and a verification boolean", async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema_version: "w11-audit-event-list/1.0",
            items: [
              {
                schema_version: "w11-audit-event/1.0",
                event_id: "aud_syn_alpha_event_0001",
                organization_id: organizationId,
                sequence: 1,
                event_type: "risk_classified",
                previous_hash: "0".repeat(64),
                event_hash: "c".repeat(64),
                payload_hash: "d".repeat(64),
                created_at: "2026-07-29T12:00:00Z",
              },
            ],
            count: 1,
            head_sequence: 1,
            head_hash: "c".repeat(64),
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            schema_version: "w11-audit-verification/1.0",
            valid: true,
            event_count: 2,
            head_sequence: 2,
            head_hash: "e".repeat(64),
            reason: "valid",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );

    const audit = await loadAuditEvents(organizationId);
    expect(audit.events[0]?.eventType).toBe("risk_classified");
    expect(audit.headSequence).toBe(1);
    expect(audit.headHash).toBe("c".repeat(64));
    expect(await verifyAuditChain(organizationId)).toBe(true);
  });
});
