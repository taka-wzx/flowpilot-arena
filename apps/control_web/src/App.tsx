import { useEffect, useState } from "react";

import "./App.css";
import {
  ForbiddenError,
  clearInMemoryAuth,
  handleCallback,
  hasInMemoryToken,
  loadCurrentIdentity,
  logoutUrl,
  prepareLogin,
  type CurrentIdentity,
} from "./auth";

type ViewState =
  | Readonly<{ kind: "signed_out" }>
  | Readonly<{ kind: "loading" }>
  | Readonly<{ kind: "authenticated"; identity: CurrentIdentity }>
  | Readonly<{ kind: "forbidden" }>
  | Readonly<{ kind: "failed" }>;

function App() {
  const [view, setView] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    const initialize = async () => {
      try {
        if (window.location.pathname === "/callback") {
          const callbackUrl = window.location.href;
          window.history.replaceState(null, "", "/");
          await handleCallback(callbackUrl);
        } else if (!hasInMemoryToken()) {
          if (active) setView({ kind: "signed_out" });
          return;
        }
        const identity = await loadCurrentIdentity();
        if (active) setView({ kind: "authenticated", identity });
      } catch (error) {
        if (!active) return;
        if (error instanceof ForbiddenError) {
          setView({ kind: "forbidden" });
        } else {
          clearInMemoryAuth();
          setView({ kind: "failed" });
        }
      }
    };
    void initialize();
    return () => {
      active = false;
    };
  }, []);

  const login = async () => {
    setView({ kind: "loading" });
    try {
      window.location.assign(await prepareLogin());
    } catch {
      clearInMemoryAuth();
      setView({ kind: "failed" });
    }
  };

  const logout = () => {
    window.location.assign(logoutUrl());
  };

  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">W10 / Identity boundary</p>
        <h1 id="page-title">FlowPilot Arena</h1>
        <p className="lead">
          Local OIDC authentication with database-backed organization membership and closed RBAC.
        </p>
      </section>

      {view.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h2>Checking identity</h2>
          <p>Validating the local OIDC transaction and server authorization.</p>
        </section>
      )}

      {view.kind === "signed_out" && (
        <section className="card">
          <h2>Sign in</h2>
          <p>Use the fixed local Keycloak realm with Authorization Code and PKCE.</p>
          <button type="button" onClick={() => void login()}>
            Sign in with local OIDC
          </button>
        </section>
      )}

      {view.kind === "authenticated" && (
        <section className="card" aria-labelledby="identity-title">
          <h2 id="identity-title">Current identity</h2>
          <dl>
            <div>
              <dt>Organization</dt>
              <dd>{view.identity.organizationId}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{view.identity.role}</dd>
            </div>
          </dl>
          <button type="button" onClick={logout}>
            Sign out
          </button>
        </section>
      )}

      {view.kind === "forbidden" && (
        <section className="card status-card" role="alert">
          <h2>Forbidden</h2>
          <p>The identity is valid, but its current database membership is not authorized.</p>
          <button type="button" onClick={logout}>
            Sign out
          </button>
        </section>
      )}

      {view.kind === "failed" && (
        <section className="card status-card" role="alert">
          <h2>Identity check failed</h2>
          <p>The callback, token, or current identity response was rejected.</p>
          <button type="button" onClick={() => setView({ kind: "signed_out" })}>
            Return to sign in
          </button>
        </section>
      )}

      <p className="footnote">
        Tokens stay in memory and never authorize from browser-visible role or organization state.
      </p>
    </main>
  );
}

export default App;
