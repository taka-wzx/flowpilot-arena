import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { ApprovalRequest, ApprovalRole, AuditSnapshot } from "../approval";
import { ForbiddenError, type CurrentIdentity } from "../auth";
import {
  createDemoIdempotencyKey,
  isTerminalRun,
  loadProductionRun,
  loadProductionRuns,
  loadProductionRunTrace,
  startRunPolling,
  submitDemoRun,
  type DemoProcess,
  type ProductionRun,
  type RunTrace,
} from "../runs";
import RunTimeline from "./RunTimeline";

type DemoConsoleProps = Readonly<{
  identity: CurrentIdentity;
  approvalRoles: readonly ApprovalRole[];
  requests: readonly ApprovalRequest[];
  audit: AuditSnapshot;
  auditValid: boolean | null;
  notice: string | null;
  onDecide: (requestId: string, decision: "approved" | "rejected") => Promise<void>;
  onVerifyAudit: () => Promise<void>;
  onLogout: () => void;
}>;

type ListState =
  | Readonly<{ kind: "loading" }>
  | Readonly<{ kind: "ready"; runs: readonly ProductionRun[] }>
  | Readonly<{ kind: "forbidden" }>
  | Readonly<{ kind: "failed" }>;

type DetailState =
  | Readonly<{ kind: "idle" }>
  | Readonly<{ kind: "loading" }>
  | Readonly<{ kind: "ready"; run: ProductionRun }>
  | Readonly<{ kind: "forbidden" }>
  | Readonly<{ kind: "failed" }>;

type TraceState =
  | Readonly<{ kind: "idle" }>
  | Readonly<{ kind: "loading" }>
  | Readonly<{ kind: "ready"; trace: RunTrace }>
  | Readonly<{ kind: "unavailable" }>
  | Readonly<{ kind: "failed" }>;

type SubmissionState =
  | Readonly<{ kind: "idle" }>
  | Readonly<{ kind: "submitting"; process: DemoProcess }>
  | Readonly<{ kind: "accepted"; runId: string }>
  | Readonly<{ kind: "failed" }>;

const PROCESS_LABELS: Record<DemoProcess, string> = {
  joiner: "Joiner",
  mover: "Mover",
  leaver: "Leaver",
};

const formatTimestamp = (value: string): string =>
  new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));

function DemoConsole({
  identity,
  approvalRoles,
  requests,
  audit,
  auditValid,
  notice,
  onDecide,
  onVerifyAudit,
  onLogout,
}: DemoConsoleProps) {
  const [listState, setListState] = useState<ListState>({ kind: "loading" });
  const [detailState, setDetailState] = useState<DetailState>({ kind: "idle" });
  const [traceState, setTraceState] = useState<TraceState>({ kind: "idle" });
  const [submission, setSubmission] = useState<SubmissionState>({ kind: "idle" });
  const [filter, setFilter] = useState<"all" | "active" | "terminal">("all");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [pollingGeneration, setPollingGeneration] = useState(0);
  const [pollingStale, setPollingStale] = useState(false);
  const [pollingFailed, setPollingFailed] = useState(false);
  const idempotencyKeys = useRef<Partial<Record<DemoProcess, string>>>({});
  const pollingRun = useRef<ProductionRun | null>(null);
  const canReadTrace = identity.permissions.includes("observability.trace.read");
  const canSubmit = identity.permissions.includes("production.run.submit");

  const refreshRuns = useCallback(async (showLoading = true) => {
    if (showLoading) setListState({ kind: "loading" });
    try {
      const runs = await loadProductionRuns(identity.organizationId);
      setListState({ kind: "ready", runs });
    } catch (error) {
      setListState(error instanceof ForbiddenError ? { kind: "forbidden" } : { kind: "failed" });
    }
  }, [identity.organizationId]);

  const refreshTrace = useCallback(async (runId: string) => {
    if (!canReadTrace) {
      setTraceState({ kind: "unavailable" });
      return;
    }
    setTraceState({ kind: "loading" });
    try {
      const trace = await loadProductionRunTrace(identity.organizationId, runId);
      setTraceState({ kind: "ready", trace });
    } catch (error) {
      setTraceState(error instanceof ForbiddenError ? { kind: "unavailable" } : { kind: "failed" });
    }
  }, [canReadTrace, identity.organizationId]);

  const openRun = useCallback(async (runId: string) => {
    setSelectedRunId(runId);
    setDetailState({ kind: "loading" });
    setPollingStale(false);
    setPollingFailed(false);
    setPollingGeneration((value) => value + 1);
    void refreshTrace(runId);
    try {
      const run = await loadProductionRun(identity.organizationId, runId);
      pollingRun.current = run;
      setDetailState({ kind: "ready", run });
    } catch (error) {
      setDetailState(error instanceof ForbiddenError ? { kind: "forbidden" } : { kind: "failed" });
    }
  }, [identity.organizationId, refreshTrace]);

  useEffect(() => {
    let active = true;
    const loadInitialRuns = async () => {
      try {
        const runs = await loadProductionRuns(identity.organizationId);
        if (active) setListState({ kind: "ready", runs });
      } catch (error) {
        if (active) {
          setListState(error instanceof ForbiddenError ? { kind: "forbidden" } : { kind: "failed" });
        }
      }
    };
    void loadInitialRuns();
    return () => {
      active = false;
    };
  }, [identity.organizationId]);

  const pollTarget =
    detailState.kind === "ready" && !isTerminalRun(detailState.run.status)
      ? `${detailState.run.runId}:${pollingGeneration}`
      : null;

  useEffect(() => {
    const initialRun = pollingRun.current;
    if (pollTarget === null || initialRun === null || !pollTarget.startsWith(`${initialRun.runId}:`)) return;
    return startRunPolling({
      organizationId: identity.organizationId,
      initialRun,
      onUpdate: (run) => {
        pollingRun.current = run;
        setDetailState({ kind: "ready", run });
        setListState((current) =>
          current.kind === "ready"
            ? {
                kind: "ready",
                runs: current.runs.map((item) => item.runId === run.runId ? run : item),
              }
            : current,
        );
        if (isTerminalRun(run.status)) void refreshTrace(run.runId);
      },
      onError: (error) => {
        setPollingFailed(true);
        if (error instanceof ForbiddenError) setDetailState({ kind: "forbidden" });
      },
      onTimeout: () => setPollingStale(true),
    });
  }, [identity.organizationId, pollTarget, refreshTrace]);

  const runs = useMemo(() => listState.kind === "ready" ? listState.runs : [], [listState]);
  const activeCount = runs.filter((run) => !isTerminalRun(run.status)).length;
  const terminalCount = runs.length - activeCount;
  const pendingApprovals = requests.filter((request) => request.status === "pending").length;
  const filteredRuns = useMemo(
    () => runs.filter((run) =>
      filter === "all" || (filter === "active" ? !isTerminalRun(run.status) : isTerminalRun(run.status)),
    ),
    [filter, runs],
  );

  const submit = async (process: DemoProcess) => {
    if (!canSubmit || submission.kind === "submitting") return;
    const key = idempotencyKeys.current[process] ?? createDemoIdempotencyKey(process);
    idempotencyKeys.current[process] = key;
    setSubmission({ kind: "submitting", process });
    try {
      const run = await submitDemoRun(identity.organizationId, process, key);
      delete idempotencyKeys.current[process];
      setSubmission({ kind: "accepted", runId: run.runId });
      setListState((current) => {
        if (current.kind !== "ready") return { kind: "ready", runs: [run] };
        const withoutReplay = current.runs.filter((item) => item.runId !== run.runId);
        return { kind: "ready", runs: [run, ...withoutReplay] };
      });
      void openRun(run.runId);
    } catch {
      setSubmission({ kind: "failed" });
    }
  };

  const refreshSelected = async () => {
    setPollingStale(false);
    setPollingFailed(false);
    setPollingGeneration((value) => value + 1);
    await refreshRuns(false);
    if (selectedRunId !== null) await openRun(selectedRunId);
  };

  const linkedApproval =
    detailState.kind === "ready" && detailState.run.approvalRequestId !== null
      ? requests.find((request) => request.requestId === detailState.run.approvalRequestId) ?? null
      : null;

  return (
    <>
      <header className="console-header">
        <div>
          <div className="environment-badge"><span aria-hidden="true" /> SYNTHETIC LOCAL DEMO</div>
          <p className="eyebrow">W17 / Portfolio Demo Console</p>
          <h1 id="page-title">FlowPilot Arena</h1>
          <p className="lead">
            A bounded view of synthetic identity workflows, approvals, audit evidence, and Agent state.
          </p>
        </div>
        <div className="header-actions">
          <a className="secondary-action" href="http://127.0.0.1:5174" target="_blank" rel="noreferrer">
            Open Sandbox <span aria-hidden="true">↗</span>
          </a>
          <button className="quiet-button" type="button" onClick={onLogout}>Sign out</button>
        </div>
      </header>

      <section className="overview-section" aria-labelledby="overview-title">
        <div className="section-heading">
          <div>
            <p className="section-kicker">At a glance</p>
            <h2 id="overview-title">Overview</h2>
          </div>
          <button className="quiet-button" type="button" onClick={() => void refreshSelected()}>
            Refresh console
          </button>
        </div>
        <div className="overview-grid">
          <article className="metric-card identity-card">
            <span>Current identity</span>
            <strong>{identity.userId}</strong>
            <small>{identity.organizationId} · {identity.role.replaceAll("_", " ")}</small>
          </article>
          <article className="metric-card">
            <span>Active runs</span>
            <strong>{listState.kind === "ready" ? activeCount : "—"}</strong>
            <small>Synthetic, non-terminal</small>
          </article>
          <article className="metric-card">
            <span>Terminal runs</span>
            <strong>{listState.kind === "ready" ? terminalCount : "—"}</strong>
            <small>Agent state only</small>
          </article>
          <article className="metric-card">
            <span>Pending approvals</span>
            <strong>{pendingApprovals}</strong>
            <small>{approvalRoles.length > 0 ? `Authority: ${approvalRoles.join(" + ")}` : "No decision authority"}</small>
          </article>
          <article className="metric-card">
            <span>Audit chain</span>
            <strong>{auditValid === null ? "Not verified" : auditValid ? "Verified" : "Failed"}</strong>
            <small>{audit.events.length} events · head #{audit.headSequence}</small>
          </article>
        </div>
      </section>

      <div className="console-grid">
        <div className="console-column">
          <section className="panel" aria-labelledby="create-run-title">
            <div className="section-heading">
              <div>
                <p className="section-kicker">Fixed inputs</p>
                <h2 id="create-run-title">Create synthetic task</h2>
              </div>
            </div>
            <p className="muted-copy">
              Select one closed JML workflow. The organization, task schema, action, and parameters are fixed.
            </p>
            <div className="process-grid">
              {(["joiner", "mover", "leaver"] as const).map((process) => (
                <button
                  className="process-button"
                  type="button"
                  key={process}
                  disabled={!canSubmit || submission.kind === "submitting"}
                  onClick={() => void submit(process)}
                >
                  <span>{PROCESS_LABELS[process]}</span>
                  <small>Submit fixed {process} plan</small>
                </button>
              ))}
            </div>
            {!canSubmit && <p role="status">Current role cannot submit production-run API records.</p>}
            {submission.kind === "submitting" && <p role="status">Submitting fixed {submission.process} task…</p>}
            {submission.kind === "accepted" && (
              <p role="status">Run {submission.runId} accepted or safely idempotency-replayed.</p>
            )}
            {submission.kind === "failed" && (
              <p className="error-copy" role="alert">Submission failed. Retry reuses the same in-memory idempotency key.</p>
            )}
          </section>

          <section className="panel" aria-labelledby="runs-title">
            <div className="section-heading runs-heading">
              <div>
                <p className="section-kicker">Organization scope</p>
                <h2 id="runs-title">Synthetic Runs</h2>
              </div>
              <label className="filter-label">
                Status
                <select value={filter} onChange={(event) => setFilter(event.target.value as typeof filter)}>
                  <option value="all">All</option>
                  <option value="active">Active</option>
                  <option value="terminal">Terminal</option>
                </select>
              </label>
            </div>

            {listState.kind === "loading" && <p className="state-copy" aria-live="polite">Loading synthetic runs…</p>}
            {listState.kind === "forbidden" && (
              <div className="inline-state is-error" role="alert">
                <strong>Run access forbidden</strong>
                <span>This authenticated membership cannot read organization runs.</span>
              </div>
            )}
            {listState.kind === "failed" && (
              <div className="inline-state is-error" role="alert">
                <strong>Runs unavailable</strong>
                <span>The response failed strict validation or the request failed.</span>
                <button type="button" onClick={() => void refreshRuns()}>Try again</button>
              </div>
            )}
            {listState.kind === "ready" && runs.length === 0 && (
              <div className="inline-state">
                <strong>No synthetic runs yet</strong>
                <span>Create one of the fixed JML tasks above.</span>
              </div>
            )}
            {listState.kind === "ready" && runs.length > 0 && filteredRuns.length === 0 && (
              <div className="inline-state">
                <strong>No runs match this filter</strong>
                <span>Change the client-side status filter to view other runs.</span>
              </div>
            )}
            {filteredRuns.length > 0 && (
              <ul className="run-list">
                {filteredRuns.map((run) => (
                  <li key={run.runId}>
                    <button
                      type="button"
                      className={selectedRunId === run.runId ? "run-row is-selected" : "run-row"}
                      aria-pressed={selectedRunId === run.runId}
                      onClick={() => void openRun(run.runId)}
                    >
                      <span className={`status-dot status-${run.status}`} aria-hidden="true" />
                      <span className="run-main">
                        <strong>{PROCESS_LABELS[run.process]} · {run.taskId}</strong>
                        <small>{run.runId}</small>
                      </span>
                      <span className={`status-pill status-${run.status}`}>{run.status.replaceAll("_", " ")}</span>
                      <time dateTime={run.updatedAt}>{formatTimestamp(run.updatedAt)} UTC</time>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <section className="panel detail-panel" aria-labelledby="run-detail-title">
          <div className="section-heading">
            <div>
              <p className="section-kicker">Selected evidence</p>
              <h2 id="run-detail-title">Run Detail</h2>
            </div>
            {selectedRunId !== null && (
              <button className="quiet-button" type="button" onClick={() => void refreshSelected()}>
                Refresh run
              </button>
            )}
          </div>

          {detailState.kind === "idle" && (
            <div className="detail-placeholder">
              <span aria-hidden="true">↖</span>
              <p>Select a synthetic run to inspect its bounded lifecycle evidence.</p>
            </div>
          )}
          {detailState.kind === "loading" && <p className="state-copy" aria-live="polite">Loading run detail…</p>}
          {detailState.kind === "forbidden" && (
            <div className="inline-state is-error" role="alert">
              <strong>Run detail forbidden</strong>
              <span>The current membership cannot read this run.</span>
            </div>
          )}
          {detailState.kind === "failed" && (
            <div className="inline-state is-error" role="alert">
              <strong>Run detail unavailable</strong>
              <span>The API request or strict response validation failed.</span>
            </div>
          )}
          {(pollingStale || pollingFailed) && (
            <div className="inline-state is-warning" role="status">
              <strong>{pollingStale ? "Stale run view" : "Automatic refresh stopped"}</strong>
              <span>{pollingStale ? "The bounded polling window ended." : "A polling request failed."} Use manual refresh to continue.</span>
            </div>
          )}

          {detailState.kind === "ready" && (
            <div className="detail-content">
              <div className="run-title-row">
                <div>
                  <span>{PROCESS_LABELS[detailState.run.process]} workflow</span>
                  <h3>{detailState.run.taskId}</h3>
                  <code>{detailState.run.runId}</code>
                </div>
                <span className={`status-pill status-${detailState.run.status}`}>
                  {detailState.run.status.replaceAll("_", " ")}
                </span>
              </div>

              <dl className="detail-facts">
                <div><dt>Action</dt><dd>{detailState.run.actionType}</dd></div>
                <div><dt>Version</dt><dd>{detailState.run.version}</dd></div>
                <div><dt>Audit sequence</dt><dd>#{detailState.run.auditSequence}</dd></div>
                <div><dt>Updated</dt><dd><time dateTime={detailState.run.updatedAt}>{formatTimestamp(detailState.run.updatedAt)} UTC</time></dd></div>
              </dl>

              {detailState.run.status === "waiting_approval" && (
                <section className="approval-callout" aria-labelledby="linked-approval-title">
                  <div>
                    <p className="section-kicker">High-risk gate</p>
                    <h3 id="linked-approval-title">Waiting for approval</h3>
                  </div>
                  {linkedApproval === null ? (
                    <p>The run references an approval not available from the current list surface.</p>
                  ) : (
                    <>
                      <p>{linkedApproval.actionType} · {linkedApproval.riskLevel} · {linkedApproval.status}</p>
                      {linkedApproval.status === "pending" && approvalRoles.length > 0 && (
                        <div className="button-row">
                          <button type="button" onClick={() => void onDecide(linkedApproval.requestId, "approved")}>Approve</button>
                          <button className="danger-button" type="button" onClick={() => void onDecide(linkedApproval.requestId, "rejected")}>Reject</button>
                        </div>
                      )}
                    </>
                  )}
                </section>
              )}
              {notice !== null && <p role="status" className="notice-copy">{notice}</p>}

              <RunTimeline
                run={detailState.run}
                trace={traceState.kind === "ready" ? traceState.trace : null}
              />
              {traceState.kind === "loading" && <p className="state-copy" aria-live="polite">Loading constrained trace…</p>}
              {traceState.kind === "unavailable" && <p className="muted-copy">Trace/replay unavailable for the current permission surface.</p>}
              {traceState.kind === "failed" && <p className="error-copy" role="alert">Trace/replay failed strict validation or could not be loaded.</p>}

              <section className="result-card" aria-labelledby="result-title">
                <p className="section-kicker">Result boundary</p>
                <h3 id="result-title">Agent and Grader are separate</h3>
                <dl>
                  <div>
                    <dt>Agent terminal status</dt>
                    <dd>{detailState.run.status}</dd>
                  </div>
                  <div>
                    <dt>Independent Grader</dt>
                    <dd>Grader result unavailable from this surface</dd>
                  </div>
                </dl>
                {detailState.run.status === "finished_ungraded" && (
                  <p>Agent execution finished, but business success has not been determined here.</p>
                )}
              </section>
            </div>
          )}
        </section>
      </div>

      <section className="audit-strip" aria-labelledby="audit-title">
        <div>
          <p className="section-kicker">Tamper-evident metadata</p>
          <h2 id="audit-title">Audit chain</h2>
          <p>{audit.events.length} append-only event references; current head sequence #{audit.headSequence}.</p>
        </div>
        {identity.permissions.includes("audit.verify") && (
          <button className="quiet-button" type="button" onClick={() => void onVerifyAudit()}>
            Verify audit chain
          </button>
        )}
      </section>

      <footer className="console-footer">
        <p>Local synthetic evidence only. “production-runs” is a historical API name, not a production claim.</p>
        <p>Access credentials remain in memory; sensitive trace fields are rejected and never rendered.</p>
      </footer>
    </>
  );
}

export default DemoConsole;
