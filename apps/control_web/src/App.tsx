import "./App.css";

const foundationBoundaries = [
  "No Sandbox or enterprise application pages",
  "No agent loop, browser automation, VLM, or model calls",
  "No Temporal workflow, external integration, or task evaluation",
] as const;

function App() {
  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">W1 / Foundation</p>
        <h1 id="page-title">FlowPilot Arena</h1>
        <p className="lead">
          A governed starting point for a future enterprise computer-use agent
          and resettable evaluation arena.
        </p>
      </section>

      <section className="card" aria-labelledby="available-title">
        <h2 id="available-title">Available now</h2>
        <ul>
          <li>A static React/Vite control-plane landing page</li>
          <li>A FastAPI health-check service at <code>/healthz</code></li>
          <li>Locked dependencies and CI quality gates</li>
        </ul>
      </section>

      <section className="card" aria-labelledby="boundary-title">
        <h2 id="boundary-title">Intentionally deferred</h2>
        <ul>
          {foundationBoundaries.map((boundary) => (
            <li key={boundary}>{boundary}</li>
          ))}
        </ul>
      </section>

      <p className="footnote">
        This page makes no API, model, analytics, or external-service calls.
      </p>
    </main>
  );
}

export default App;
