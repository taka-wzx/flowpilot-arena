import type { ProductionRun, RunTrace } from "../runs";

type RunTimelineProps = Readonly<{
  run: ProductionRun;
  trace: RunTrace | null;
}>;

const formatTimestamp = (value: string): string =>
  new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(value));

const traceTime = (trace: RunTrace | null, phases: readonly string[]): string | null =>
  trace?.events.find((event) => phases.includes(event.phase))?.observedAt ?? null;

function RunTimeline({ run, trace }: RunTimelineProps) {
  const stages = [
    { label: "Observe", time: run.acceptedAt, detail: "Run accepted by the existing Control API." },
    {
      label: "Plan",
      time: traceTime(trace, ["planning"]) ?? run.queuedAt,
      detail: "Typed planning evidence, when returned by the trace surface.",
    },
    {
      label: "Execute",
      time: run.startedAt ?? traceTime(trace, ["workflow", "browser"]),
      detail: "Agent execution start from run or bounded trace metadata.",
    },
    {
      label: "Recover",
      time: traceTime(trace, ["recovery"]),
      detail: "Shown only when the API records recovery evidence.",
    },
    {
      label: "Verify",
      time: traceTime(trace, ["grader", "terminal"]) ?? run.finishedAt,
      detail: "Agent terminal evidence; this is not an independent Grader verdict.",
    },
  ] as const;

  return (
    <section className="timeline-panel" aria-labelledby="timeline-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Lifecycle evidence</p>
          <h3 id="timeline-title">Observe → plan → execute → recover → verify</h3>
        </div>
      </div>
      <ol className="run-timeline">
        {stages.map((stage) => (
          <li key={stage.label} className={stage.time === null ? "is-pending" : "is-observed"}>
            <span className="timeline-marker" aria-hidden="true" />
            <div>
              <strong>{stage.label}</strong>
              {stage.time === null ? (
                <span>Not observed</span>
              ) : (
                <time dateTime={stage.time}>{formatTimestamp(stage.time)} UTC</time>
              )}
              <p>{stage.detail}</p>
            </div>
          </li>
        ))}
      </ol>

      {trace !== null && (
        <div className="trace-grid">
          <details>
            <summary>Bounded trace events ({trace.events.length})</summary>
            {trace.events.length === 0 ? (
              <p>No trace events returned.</p>
            ) : (
              <ol className="evidence-list">
                {trace.events.map((event) => (
                  <li key={event.sequence}>
                    <span>#{event.sequence}</span>
                    <strong>{event.phase}</strong>
                    <span>{event.status} · {event.reason}</span>
                    <time dateTime={event.observedAt}>{formatTimestamp(event.observedAt)} UTC</time>
                  </li>
                ))}
              </ol>
            )}
          </details>
          <details>
            <summary>Constrained replay ({trace.replaySteps.length})</summary>
            {trace.replaySteps.length === 0 ? (
              <p>No replay steps returned.</p>
            ) : (
              <ol className="evidence-list">
                {trace.replaySteps.map((step) => (
                  <li key={step.ordinal}>
                    <span>#{step.ordinal}</span>
                    <strong>{step.phase}</strong>
                    <span>{step.status} · {step.reason}</span>
                    <time dateTime={step.observedAt}>{formatTimestamp(step.observedAt)} UTC</time>
                  </li>
                ))}
              </ol>
            )}
          </details>
        </div>
      )}
    </section>
  );
}

export default RunTimeline;
