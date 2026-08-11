import "@testing-library/jest-dom/vitest";

import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ApprovalRequest, AuditSnapshot } from "../approval";
import { ForbiddenError, type CurrentIdentity } from "../auth";
import type { ProductionRun, RunTrace } from "../runs";

const mocks = vi.hoisted(() => ({
  createDemoIdempotencyKey: vi.fn(() => "w17-demo-joiner-00112233445566778899aabb"),
  loadProductionRun: vi.fn(),
  loadProductionRuns: vi.fn(),
  loadProductionRunTrace: vi.fn(),
  startRunPolling: vi.fn((options: { onTimeout: () => void }) => {
    void options;
    return vi.fn();
  }),
  submitDemoRun: vi.fn(),
}));

vi.mock("../runs", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../runs")>();
  return {
    ...actual,
    createDemoIdempotencyKey: mocks.createDemoIdempotencyKey,
    loadProductionRun: mocks.loadProductionRun,
    loadProductionRuns: mocks.loadProductionRuns,
    loadProductionRunTrace: mocks.loadProductionRunTrace,
    startRunPolling: mocks.startRunPolling,
    submitDemoRun: mocks.submitDemoRun,
  };
});

import DemoConsole from "./DemoConsole";

const organizationId = "org_syn_alpha_0001";
const runId = "run_syn_alpha_0001";

const makeRun = (overrides: Partial<ProductionRun> = {}): ProductionRun => ({
  runId,
  organizationId,
  taskId: "w7-jml-joiner-001-v1",
  process: "joiner",
  category: "standard_joiner",
  approvalRequestId: null,
  actionType: "generate_plan",
  status: "queued",
  version: 1,
  acceptedAt: "2026-08-11T01:00:00Z",
  queuedAt: "2026-08-11T01:00:01Z",
  startedAt: null,
  finishedAt: null,
  updatedAt: "2026-08-11T01:00:01Z",
  terminalReason: null,
  receiptReference: null,
  auditSequence: 1,
  ...overrides,
});

const traceFor = (run: ProductionRun): RunTrace => ({
  run,
  terminalStatus: run.status,
  failureCategory: "none",
  events: [],
  replaySteps: [],
});

const identity: CurrentIdentity = {
  userId: "usr_syn_alpha_admin_0001",
  organizationId,
  membershipId: "mbr_syn_alpha_admin_0001",
  role: "organization_admin",
  permissions: [
    "production.run.read",
    "production.run.submit",
    "observability.trace.read",
    "approval.request.read",
    "approval.request.decide",
    "audit.read",
    "audit.verify",
  ],
  authorizationHash: "a".repeat(64),
};

const audit: AuditSnapshot = {
  events: [{ eventId: "aud_syn_alpha_0001", sequence: 1, eventType: "run_queued", eventHash: "b".repeat(64) }],
  headSequence: 1,
  headHash: "b".repeat(64),
};

const defaultProps = () => ({
  identity,
  approvalRoles: ["manager" as const],
  requests: [] as readonly ApprovalRequest[],
  audit,
  auditValid: null,
  notice: null,
  onDecide: vi.fn().mockResolvedValue(undefined),
  onVerifyAudit: vi.fn().mockResolvedValue(undefined),
  onLogout: vi.fn(),
});

describe("DemoConsole", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    window.sessionStorage.clear();
    mocks.loadProductionRuns.mockResolvedValue([]);
    mocks.startRunPolling.mockReturnValue(vi.fn());
  });

  it("renders the local environment, overview, Sandbox entry, and empty state", async () => {
    render(<DemoConsole {...defaultProps()} />);

    expect(screen.getByText("SYNTHETIC LOCAL DEMO")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByText("usr_syn_alpha_admin_0001")).toBeInTheDocument();
    expect(await screen.findByText("No synthetic runs yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open sandbox/iu })).toHaveAttribute("href", "http://127.0.0.1:5174");
    expect(screen.getByRole("button", { name: /joiner/iu })).toHaveProperty("tabIndex", 0);
    expect(screen.getByLabelText("Status")).toHaveProperty("tabIndex", 0);
  });

  it("renders loading, forbidden, and failure list states", async () => {
    mocks.loadProductionRuns.mockReturnValueOnce(new Promise(() => undefined));
    const loading = render(<DemoConsole {...defaultProps()} />);
    expect(screen.getByText("Loading synthetic runs…")).toBeInTheDocument();
    loading.unmount();

    mocks.loadProductionRuns.mockRejectedValueOnce(new ForbiddenError("forbidden"));
    const forbidden = render(<DemoConsole {...defaultProps()} />);
    expect(await screen.findByText("Run access forbidden")).toBeInTheDocument();
    forbidden.unmount();

    mocks.loadProductionRuns.mockRejectedValueOnce(new Error("invalid"));
    render(<DemoConsole {...defaultProps()} />);
    expect(await screen.findByText("Runs unavailable")).toBeInTheDocument();
  });

  it("shows strict Agent/Grader separation for finished_ungraded", async () => {
    const terminal = makeRun({
      status: "finished_ungraded",
      version: 5,
      startedAt: "2026-08-11T01:00:02Z",
      finishedAt: "2026-08-11T01:00:05Z",
      updatedAt: "2026-08-11T01:00:05Z",
      terminalReason: "agent_finished",
    });
    mocks.loadProductionRuns.mockResolvedValue([terminal]);
    mocks.loadProductionRun.mockResolvedValue(terminal);
    mocks.loadProductionRunTrace.mockResolvedValue(traceFor(terminal));
    render(<DemoConsole {...defaultProps()} />);

    const row = await screen.findByRole("button", { name: /joiner.*w7-jml-joiner-001-v1/iu });
    row.focus();
    expect(row).toHaveFocus();
    fireEvent.click(row);

    expect(await screen.findByRole("heading", { name: "Agent and Grader are separate" })).toBeInTheDocument();
    expect(screen.getByText("Grader result unavailable from this surface")).toBeInTheDocument();
    expect(screen.getByText(/business success has not been determined/iu)).toBeInTheDocument();
    expect(mocks.startRunPolling).not.toHaveBeenCalled();
  });

  it("links a waiting run to the existing approval decision handler", async () => {
    const waiting = makeRun({
      status: "waiting_approval",
      queuedAt: null,
      approvalRequestId: "apr_syn_alpha_0001",
    });
    const request: ApprovalRequest = {
      requestId: "apr_syn_alpha_0001",
      organizationId,
      taskId: "w7-jml-joiner-001-v1",
      stepId: "assign_asset",
      actionType: "assign_asset",
      parameterHash: "c".repeat(64),
      riskLevel: "L2",
      requiredRoles: ["manager"],
      status: "pending",
      version: 1,
      expiresAt: "2026-08-11T02:00:00Z",
    };
    const props = { ...defaultProps(), requests: [request] };
    mocks.loadProductionRuns.mockResolvedValue([waiting]);
    mocks.loadProductionRun.mockResolvedValue(waiting);
    mocks.loadProductionRunTrace.mockResolvedValue(traceFor(waiting));
    render(<DemoConsole {...props} />);

    fireEvent.click(await screen.findByRole("button", { name: /joiner.*w7-jml/iu }));
    fireEvent.click(await screen.findByRole("button", { name: "Approve" }));
    expect(props.onDecide).toHaveBeenCalledWith("apr_syn_alpha_0001", "approved");
  });

  it("submits a fixed task and renders success and failure states", async () => {
    const accepted = makeRun();
    mocks.submitDemoRun.mockResolvedValueOnce(accepted);
    mocks.loadProductionRun.mockResolvedValue(accepted);
    mocks.loadProductionRunTrace.mockResolvedValue(traceFor(accepted));
    render(<DemoConsole {...defaultProps()} />);

    fireEvent.click(screen.getByRole("button", { name: /joiner/iu }));
    expect(await screen.findByText(/accepted or safely idempotency-replayed/iu)).toBeInTheDocument();
    expect(mocks.submitDemoRun).toHaveBeenCalledWith(
      organizationId,
      "joiner",
      "w17-demo-joiner-00112233445566778899aabb",
    );

    mocks.submitDemoRun.mockRejectedValueOnce(new Error("failed"));
    fireEvent.click(screen.getByRole("button", { name: /mover/iu }));
    expect(await screen.findByText(/submission failed/iu)).toBeInTheDocument();
  });

  it("starts bounded polling, reports stale state, and cleans up on unmount", async () => {
    const active = makeRun();
    const cleanup = vi.fn();
    mocks.startRunPolling.mockReturnValue(cleanup);
    mocks.loadProductionRuns.mockResolvedValue([active]);
    mocks.loadProductionRun.mockResolvedValue(active);
    mocks.loadProductionRunTrace.mockResolvedValue(traceFor(active));
    const rendered = render(<DemoConsole {...defaultProps()} />);

    fireEvent.click(await screen.findByRole("button", { name: /joiner.*w7-jml/iu }));
    await waitFor(() => expect(mocks.startRunPolling).toHaveBeenCalledOnce());
    const options = mocks.startRunPolling.mock.calls[0]?.[0] as { onTimeout: () => void };
    act(() => options.onTimeout());
    expect(screen.getByText("Stale run view")).toBeInTheDocument();

    rendered.unmount();
    expect(cleanup).toHaveBeenCalled();
  });

  it("never renders or stores access, nonce, secret, hash, or raw payload material", async () => {
    const active = makeRun();
    mocks.loadProductionRuns.mockResolvedValue([active]);
    mocks.loadProductionRun.mockResolvedValue(active);
    mocks.loadProductionRunTrace.mockResolvedValue(traceFor(active));
    const { container } = render(<DemoConsole {...defaultProps()} />);
    fireEvent.click(await screen.findByRole("button", { name: /joiner.*w7-jml/iu }));
    await screen.findByRole("heading", { name: /agent and grader/iu });

    const text = container.textContent ?? "";
    expect(text).not.toContain(identity.authorizationHash);
    expect(text).not.toContain(audit.headHash);
    expect(text).not.toMatch(/runtime-access-token|runtime-nonce|client-secret|raw browser payload/iu);
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
  });
});
