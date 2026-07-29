import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  clearInMemoryAuth: vi.fn(),
  handleCallback: vi.fn(),
  hasInMemoryToken: vi.fn(),
  loadCurrentIdentity: vi.fn(),
  logoutUrl: vi.fn(() => "http://127.0.0.1:8080/logout"),
  prepareLogin: vi.fn(),
  decideApprovalRequest: vi.fn(),
  loadApprovalRequest: vi.fn(),
  loadApprovalRequests: vi.fn(),
  loadAuditEvents: vi.fn(),
  loadCurrentApprovalRoles: vi.fn(),
  verifyAuditChain: vi.fn(),
}));

vi.mock("./auth", () => ({
  ForbiddenError: class ForbiddenError extends Error {},
  clearInMemoryAuth: mocks.clearInMemoryAuth,
  handleCallback: mocks.handleCallback,
  hasInMemoryToken: mocks.hasInMemoryToken,
  loadCurrentIdentity: mocks.loadCurrentIdentity,
  logoutUrl: mocks.logoutUrl,
  prepareLogin: mocks.prepareLogin,
}));

vi.mock("./approval", () => ({
  StaleApprovalError: class StaleApprovalError extends Error {},
  decideApprovalRequest: mocks.decideApprovalRequest,
  loadApprovalRequest: mocks.loadApprovalRequest,
  loadApprovalRequests: mocks.loadApprovalRequests,
  loadAuditEvents: mocks.loadAuditEvents,
  loadCurrentApprovalRoles: mocks.loadCurrentApprovalRoles,
  verifyAuditChain: mocks.verifyAuditChain,
}));

import App from "./App";
describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState(null, "", "/");
    window.sessionStorage.clear();
    mocks.hasInMemoryToken.mockReturnValue(false);
  });

  it("shows the minimal W11 signed-out approval boundary", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "FlowPilot Arena" })).toBeInTheDocument();
    expect(screen.getByText("W11 / Approval boundary")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Sign in with local OIDC" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/grants and nonce material never enter the browser/iu)).toBeInTheDocument();
  });

  it("shows approval detail, records an ETag-bound decision, and verifies audit", async () => {
    const request = {
      requestId: "apr_syn_alpha_request_0001",
      organizationId: "org_syn_alpha_0001",
      taskId: "task_syn_alpha_0001",
      stepId: "assign_asset",
      actionType: "assign_asset",
      parameterHash: "a".repeat(64),
      riskLevel: "L2" as const,
      requiredRoles: ["manager" as const],
      status: "pending" as const,
      version: 1,
      expiresAt: "2026-07-29T12:10:00Z",
    };
    const audit = {
      events: [
        {
          eventId: "aud_syn_alpha_event_0001",
          sequence: 1,
          eventType: "approval_requested",
          eventHash: "b".repeat(64),
        },
      ],
      headSequence: 1,
      headHash: "b".repeat(64),
    };
    mocks.hasInMemoryToken.mockReturnValue(true);
    mocks.loadCurrentIdentity.mockResolvedValue({
      userId: "usr_syn_alpha_manager_0001",
      organizationId: "org_syn_alpha_0001",
      membershipId: "mbr_syn_alpha_manager_0001",
      role: "operator",
      permissions: ["approval.request.read", "approval.request.decide", "audit.read", "audit.verify"],
      authorizationHash: "c".repeat(64),
    });
    mocks.loadCurrentApprovalRoles.mockResolvedValue(["manager"]);
    mocks.loadApprovalRequests.mockResolvedValueOnce([request]).mockResolvedValueOnce([
      { ...request, status: "approved", version: 2 },
    ]);
    mocks.loadApprovalRequest.mockResolvedValue({
      request,
      etag: '"w11-approval-request-aaaaaaaaaaaaaaaaaaaaaaaa-v1"',
    });
    mocks.decideApprovalRequest.mockResolvedValue({ ...request, status: "approved", version: 2 });
    mocks.loadAuditEvents.mockResolvedValue(audit);
    mocks.verifyAuditChain.mockResolvedValue(true);

    render(<App />);

    expect(await screen.findByText("manager")).toBeInTheDocument();
    expect(screen.getByText(`Binding ${"a".repeat(64)}`)).toBeInTheDocument();
    expect(screen.getByText(`Head 1 / ${"b".repeat(64)}`)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(await screen.findByText("Decision recorded from current server state.")).toBeInTheDocument();
    expect(mocks.decideApprovalRequest).toHaveBeenCalledWith(
      "org_syn_alpha_0001",
      "apr_syn_alpha_request_0001",
      '"w11-approval-request-aaaaaaaaaaaaaaaaaaaaaaaa-v1"',
      "approved",
    );

    fireEvent.click(screen.getByRole("button", { name: "Verify audit chain" }));
    expect(await screen.findByText("Verification: valid")).toBeInTheDocument();
  });
});
