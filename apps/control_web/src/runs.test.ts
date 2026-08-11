import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { authorizedApiFetch } from "./auth";
import {
  RunRequestError,
  createDemoIdempotencyKey,
  loadProductionRun,
  loadProductionRuns,
  parseProductionRun,
  parseRunTrace,
  startRunPolling,
  submitDemoRun,
  type ProductionRun,
} from "./runs";

vi.mock("./auth", () => ({ authorizedApiFetch: vi.fn() }));

const fetchMock = vi.mocked(authorizedApiFetch);
const organizationId = "org_syn_alpha_0001";
const runId = "run_syn_alpha_0001";

const runPayload = (overrides: Record<string, unknown> = {}) => ({
  schema_version: "w12-production-run/1.0",
  run_id: runId,
  organization_id: organizationId,
  requester_user_id: "usr_syn_alpha_admin_0001",
  executor_user_id: "usr_syn_alpha_admin_0001",
  task_id: "w7-jml-joiner-001-v1",
  process: "joiner",
  category: "standard_joiner",
  approval_request_id: null,
  grant_id: null,
  execution_id: null,
  action_type: "generate_plan",
  parameter_hash: "a".repeat(64),
  authorization_hash: "b".repeat(64),
  approval_set_hash: null,
  payload_hash: "c".repeat(64),
  status: "queued",
  version: 1,
  workflow_hash: "d".repeat(64),
  fencing_token: 0,
  accepted_at: "2026-08-11T01:00:00Z",
  queued_at: "2026-08-11T01:00:01Z",
  started_at: null,
  finished_at: null,
  terminal_reason: null,
  receipt_reference: null,
  audit_sequence: 1,
  ...overrides,
});

const traceAttributes = () => ({
  schema_version: "w13-trace-attributes/1.0",
  run_status: "queued",
  approval_request_id: null,
  grant_id: null,
  execution_id: null,
  authorization_hash: "b".repeat(64),
  approval_set_hash: null,
  outbox_id: null,
  outbox_status: null,
  lease_status: null,
  workflow_hash: "d".repeat(64),
  worker_reference: null,
  receipt_reference: null,
  checkpoint_hash: null,
  audit_sequence: 1,
  version: 1,
  fencing_token: 0,
  lease_version: null,
  attempt_count: 0,
  count: null,
  event_count: null,
  step_count: null,
  checkpoint_count: null,
  activity_attempts: null,
  retries: null,
  session_recoveries: null,
  replans: null,
  route_decisions: null,
  dom_observations: null,
  images: null,
  duration_ms: null,
  latency_ms: null,
  model_calls: 0,
  input_tokens: 0,
  output_tokens: 0,
  fake_cost_microusd: 0,
  real_cost_microusd: 0,
  step_id: null,
  completed_step_ids: [],
  sensitive_fields_present: false,
});

const tracePayload = () => ({
  schema_version: "w13-run-trace-export/1.0",
  run: runPayload(),
  trace_id: "1".repeat(32),
  events: [
    {
      schema_version: "w13-observability-event/1.0",
      event_id: "obs_syn_alpha_0001",
      organization_id: organizationId,
      run_id: runId,
      event_sequence: 1,
      trace_id: "1".repeat(32),
      span_id: "2".repeat(16),
      parent_span_id: null,
      phase: "admission",
      status: "queued",
      failure_category: "none",
      reason: "admitted_queued",
      attributes: traceAttributes(),
      attributes_hash: "e".repeat(64),
      event_hash: "f".repeat(64),
      observed_at: "2026-08-11T01:00:01Z",
    },
  ],
  replay_steps: [
    {
      schema_version: "w13-replay-step/1.0",
      ordinal: 1,
      phase: "admission",
      status: "queued",
      failure_category: "none",
      reason: "admitted_queued",
      reference_hash: "7".repeat(64),
      observed_at: "2026-08-11T01:00:01Z",
    },
  ],
  cost: {
    schema_version: "w13-cost-summary/1.0",
    model_calls: 0,
    input_tokens: 0,
    output_tokens: 0,
    fake_cost_microusd: 0,
    real_cost_microusd: 0,
  },
  dashboard: {
    schema_version: "w13-trace-dashboard/1.0",
    event_count: 1,
    replay_step_count: 1,
    terminal_status: "queued",
    failure_category: "none",
    model_calls: 0,
    fake_cost_microusd: 0,
    real_cost_microusd: 0,
    sensitive_fields_present: false,
    dashboard_hash: "8".repeat(64),
  },
  export_hash: "9".repeat(64),
});

describe("W17 production run client", () => {
  beforeEach(() => fetchMock.mockReset());
  afterEach(() => vi.useRealTimers());

  it("strictly parses run list and detail responses", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify({
        schema_version: "w12-production-run-list/1.0",
        items: [runPayload()],
        count: 1,
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(runPayload()), { status: 200 }));

    const runs = await loadProductionRuns(organizationId);
    expect(runs).toHaveLength(1);
    expect(runs[0]?.updatedAt).toBe("2026-08-11T01:00:01Z");
    expect((await loadProductionRun(organizationId, runId)).runId).toBe(runId);
  });

  it("rejects extra fields, unknown status, mismatched category, and invalid IDs", () => {
    expect(() => parseProductionRun({ ...runPayload(), token: "unsafe" })).toThrow(/invalid/iu);
    expect(() => parseProductionRun(runPayload({ status: "succeeded" }))).toThrow(/invalid/iu);
    expect(() => parseProductionRun(runPayload({ category: "standard_mover" }))).toThrow(/invalid/iu);
    expect(() => parseProductionRun(runPayload({ run_id: "bad-run" }))).toThrow(/invalid/iu);
    expect(() => parseProductionRun(runPayload({ status: "failed", finished_at: null }))).toThrow(/terminal/iu);
  });

  it("returns only bounded trace/replay fields and rejects sensitive or unordered data", () => {
    const parsed = parseRunTrace(tracePayload());
    expect(parsed.events[0]).toEqual({
      sequence: 1,
      phase: "admission",
      status: "queued",
      failureCategory: "none",
      reason: "admitted_queued",
      observedAt: "2026-08-11T01:00:01Z",
    });
    expect(JSON.stringify(parsed)).not.toMatch(/authorization_hash|trace_id|span_id|reference_hash/iu);

    const sensitive = tracePayload();
    sensitive.events[0].attributes = { ...traceAttributes(), token: "unsafe" } as typeof sensitive.events[0]["attributes"];
    expect(() => parseRunTrace(sensitive)).toThrow(/attributes/iu);

    const unordered = tracePayload();
    unordered.events[0].event_sequence = 2;
    expect(() => parseRunTrace(unordered)).toThrow(/ordering/iu);

    const mismatchedTrace = tracePayload();
    mismatchedTrace.events[0].trace_id = "3".repeat(32);
    expect(() => parseRunTrace(mismatchedTrace)).toThrow(/event/iu);
  });

  it("submits one fixed body and safely replays the same idempotency key", async () => {
    fetchMock.mockImplementation(async () => new Response(JSON.stringify(runPayload()), { status: 202 }));
    const key = "w17-demo-joiner-00112233445566778899aabb";

    const first = await submitDemoRun(organizationId, "joiner", key);
    const replay = await submitDemoRun(organizationId, "joiner", key);

    expect(first.runId).toBe(replay.runId);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const call of fetchMock.mock.calls) {
      const init = call[1];
      expect((init?.headers as Record<string, string>)["Idempotency-Key"]).toBe(key);
      expect(JSON.parse(String(init?.body))).toEqual({
        schema_version: "w12-production-run-create/1.0",
        task_id: "w7-jml-joiner-001-v1",
        process: "joiner",
        category: "standard_joiner",
        action_type: "generate_plan",
        parameters: {
          schema_version: "w11-task-parameters/1.0",
          task_reference: "w7-jml-joiner-001-v1",
        },
      });
    }
  });

  it("uses a closed idempotency format and exposes submission failures", async () => {
    const cryptoProvider = {
      getRandomValues: (array: Uint8Array) => {
        array.fill(10);
        return array;
      },
    } as Crypto;
    expect(createDemoIdempotencyKey("mover", cryptoProvider)).toBe(
      "w17-demo-mover-0a0a0a0a0a0a0a0a0a0a0a0a",
    );
    fetchMock.mockResolvedValue(new Response("{}", { status: 503 }));
    await expect(submitDemoRun(organizationId, "leaver", "w17-demo-leaver-1234567890abcdef"))
      .rejects.toBeInstanceOf(RunRequestError);
  });

  it("polls at a fixed interval, stops on terminal state, and reports timeout", async () => {
    vi.useFakeTimers();
    let now = 0;
    const active = parseProductionRun(runPayload());
    const terminal = parseProductionRun(runPayload({
      status: "finished_ungraded",
      finished_at: "2026-08-11T01:00:05Z",
      terminal_reason: "agent_finished",
    }));
    const updates: ProductionRun[] = [];
    const loader = vi.fn().mockResolvedValueOnce(active).mockResolvedValueOnce(terminal);
    const onTimeout = vi.fn();
    const stop = startRunPolling({
      organizationId,
      initialRun: active,
      onUpdate: (run) => updates.push(run),
      onError: vi.fn(),
      onTimeout,
      loader,
      intervalMs: 100,
      maxDurationMs: 500,
      now: () => now,
    });

    now = 100;
    await vi.advanceTimersByTimeAsync(100);
    now = 200;
    await vi.advanceTimersByTimeAsync(100);
    await vi.advanceTimersByTimeAsync(500);
    expect(loader).toHaveBeenCalledTimes(2);
    expect(updates.at(-1)?.status).toBe("finished_ungraded");
    expect(onTimeout).not.toHaveBeenCalled();
    stop();

    const timeout = vi.fn();
    now = 0;
    startRunPolling({
      organizationId,
      initialRun: active,
      onUpdate: vi.fn(),
      onError: vi.fn(),
      onTimeout: timeout,
      loader: vi.fn().mockResolvedValue(active),
      intervalMs: 100,
      maxDurationMs: 100,
      now: () => now,
    });
    now = 100;
    await vi.advanceTimersByTimeAsync(100);
    expect(timeout).toHaveBeenCalledOnce();
  });

  it("stops polling on page hide and explicit cleanup", async () => {
    vi.useFakeTimers();
    const active = parseProductionRun(runPayload());
    const loader = vi.fn().mockResolvedValue(active);
    const stop = startRunPolling({
      organizationId,
      initialRun: active,
      onUpdate: vi.fn(),
      onError: vi.fn(),
      onTimeout: vi.fn(),
      loader,
      intervalMs: 100,
      maxDurationMs: 1_000,
    });
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
    document.dispatchEvent(new Event("visibilitychange"));
    await vi.advanceTimersByTimeAsync(500);
    expect(loader).not.toHaveBeenCalled();
    stop();
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
  });
});
