import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { ProductionRun, RunTrace } from "../runs";
import RunTimeline from "./RunTimeline";

const run: ProductionRun = {
  runId: "run_syn_alpha_0001",
  organizationId: "org_syn_alpha_0001",
  taskId: "w7-jml-joiner-001-v1",
  process: "joiner",
  category: "standard_joiner",
  approvalRequestId: null,
  actionType: "generate_plan",
  status: "finished_ungraded",
  version: 5,
  acceptedAt: "2026-08-11T01:00:00Z",
  queuedAt: "2026-08-11T01:00:01Z",
  startedAt: "2026-08-11T01:00:02Z",
  finishedAt: "2026-08-11T01:00:05Z",
  updatedAt: "2026-08-11T01:00:05Z",
  terminalReason: "agent_finished",
  receiptReference: "receipt_syn_0001",
  auditSequence: 5,
};

const trace: RunTrace = {
  run,
  terminalStatus: "finished_ungraded",
  failureCategory: "none",
  events: [
    {
      sequence: 1,
      phase: "planning",
      status: "succeeded",
      failureCategory: "none",
      reason: "planning_summary",
      observedAt: "2026-08-11T01:00:01Z",
    },
    {
      sequence: 2,
      phase: "terminal",
      status: "succeeded",
      failureCategory: "none",
      reason: "run_finished_ungraded",
      observedAt: "2026-08-11T01:00:05Z",
    },
  ],
  replaySteps: [
    {
      ordinal: 1,
      phase: "planning",
      status: "succeeded",
      failureCategory: "none",
      reason: "planning_summary",
      observedAt: "2026-08-11T01:00:01Z",
    },
  ],
};

describe("RunTimeline", () => {
  afterEach(cleanup);

  it("renders the five lifecycle stages from returned fields", () => {
    render(<RunTimeline run={run} trace={trace} />);

    expect(screen.getByRole("heading", { name: /observe.*plan.*execute.*recover.*verify/iu })).toBeInTheDocument();
    for (const label of ["Observe", "Plan", "Execute", "Recover", "Verify"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByText("Not observed")).toBeInTheDocument();
    expect(screen.getByText("Bounded trace events (2)")).toBeInTheDocument();
    expect(screen.getByText("Constrained replay (1)")).toBeInTheDocument();
  });

  it("renders no internal hash, trace identifier, or receipt value", () => {
    const { container } = render(<RunTimeline run={run} trace={trace} />);
    const text = container.textContent ?? "";

    expect(text).not.toContain("receipt_syn_0001");
    expect(text).not.toMatch(/[0-9a-f]{32,64}/u);
    expect(text).toContain("Agent terminal evidence");
  });
});
