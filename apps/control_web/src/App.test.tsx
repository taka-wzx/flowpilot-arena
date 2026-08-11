import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

vi.mock("./components/DemoConsole", () => ({
  default: (props: {
    identity: { userId: string };
    notice: string | null;
    onDecide: (requestId: string, decision: "approved" | "rejected") => Promise<void>;
    onVerifyAudit: () => Promise<void>;
  }) => (
    <section aria-label="demo console">
      <span>{props.identity.userId}</span>
      {props.notice !== null && <p>{props.notice}</p>}
      <button type="button" onClick={() => void props.onDecide("apr_syn_alpha_request_0001", "approved")}>Approve linked</button>
      <button type="button" onClick={() => void props.onVerifyAudit()}>Verify linked audit</button>
    </section>
  ),
}));

import App from "./App";

const identity = {
  userId: "usr_syn_alpha_manager_0001",
  organizationId: "org_syn_alpha_0001",
  membershipId: "mbr_syn_alpha_manager_0001",
  role: "operator",
  permissions: ["approval.request.read", "approval.request.decide", "audit.read", "audit.verify"],
  authorizationHash: "c".repeat(64),
};

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
  expiresAt: "2026-08-11T12:10:00Z",
};

const audit = {
  events: [{ eventId: "aud_syn_alpha_event_0001", sequence: 1, eventType: "approval_requested", eventHash: "b".repeat(64) }],
  headSequence: 1,
  headHash: "b".repeat(64),
};

describe("App", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState(null, "", "/");
    window.sessionStorage.clear();
    window.localStorage.clear();
    mocks.hasInMemoryToken.mockReturnValue(false);
  });

  it("shows a clearly marked synthetic local sign-in surface", async () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "FlowPilot Arena" })).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC LOCAL DEMO")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Sign in with local OIDC" })).toBeInTheDocument();
    expect(screen.getByText(/never rendered by this console/iu)).toBeInTheDocument();
  });

  it("loads the console, preserves ETag approval decisions, and verifies audit", async () => {
    mocks.hasInMemoryToken.mockReturnValue(true);
    mocks.loadCurrentIdentity.mockResolvedValue(identity);
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

    expect(await screen.findByRole("region", { name: "demo console" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve linked" }));
    expect(await screen.findByText("Decision recorded from current server state.")).toBeInTheDocument();
    expect(mocks.decideApprovalRequest).toHaveBeenCalledWith(
      "org_syn_alpha_0001",
      "apr_syn_alpha_request_0001",
      '"w11-approval-request-aaaaaaaaaaaaaaaaaaaaaaaa-v1"',
      "approved",
    );

    fireEvent.click(screen.getByRole("button", { name: "Verify linked audit" }));
    expect(mocks.verifyAuditChain).toHaveBeenCalledWith("org_syn_alpha_0001");
  });

  it("handles the callback before rendering and keeps browser storage free of credentials", async () => {
    window.history.replaceState(null, "", "/callback?code=fixed&state=fixed");
    mocks.handleCallback.mockResolvedValue(undefined);
    mocks.loadCurrentIdentity.mockResolvedValue(identity);
    mocks.loadCurrentApprovalRoles.mockResolvedValue([]);
    mocks.loadApprovalRequests.mockResolvedValue([]);
    mocks.loadAuditEvents.mockResolvedValue(audit);

    const { container } = render(<App />);
    expect(await screen.findByRole("region", { name: "demo console" })).toBeInTheDocument();
    expect(mocks.handleCallback).toHaveBeenCalledOnce();
    expect(container.textContent).not.toMatch(/runtime-access-token|runtime-nonce|client-secret/iu);
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
  });
});
