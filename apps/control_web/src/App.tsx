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
import {
  StaleApprovalError,
  decideApprovalRequest,
  loadApprovalRequest,
  loadApprovalRequests,
  loadAuditEvents,
  loadCurrentApprovalRoles,
  verifyAuditChain,
  type ApprovalRequest,
  type ApprovalRole,
  type AuditSnapshot,
} from "./approval";
import DemoConsole from "./components/DemoConsole";

type AuthenticatedData = Readonly<{
  identity: CurrentIdentity;
  approvalRoles: readonly ApprovalRole[];
  requests: readonly ApprovalRequest[];
  audit: AuditSnapshot;
  auditValid: boolean | null;
}>;

const EMPTY_AUDIT: AuditSnapshot = { events: [], headSequence: 0, headHash: "0".repeat(64) };

type ViewState =
  | Readonly<{ kind: "signed_out" }>
  | Readonly<{ kind: "loading" }>
  | Readonly<{ kind: "authenticated"; data: AuthenticatedData; notice: string | null }>
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
        const [approvalRoles, requests, audit] = await Promise.all([
          loadCurrentApprovalRoles(),
          loadApprovalRequests(identity.organizationId),
          identity.permissions.includes("audit.read")
            ? loadAuditEvents(identity.organizationId)
            : Promise.resolve(EMPTY_AUDIT),
        ]);
        if (active) {
          setView({
            kind: "authenticated",
            data: { identity, approvalRoles, requests, audit, auditValid: null },
            notice: null,
          });
        }
      } catch (error) {
        if (!active) return;
        if (error instanceof ForbiddenError) setView({ kind: "forbidden" });
        else {
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

  const decide = async (requestId: string, decision: "approved" | "rejected") => {
    if (view.kind !== "authenticated") return;
    try {
      const detail = await loadApprovalRequest(view.data.identity.organizationId, requestId);
      await decideApprovalRequest(
        view.data.identity.organizationId,
        requestId,
        detail.etag,
        decision,
      );
      const requests = await loadApprovalRequests(view.data.identity.organizationId);
      setView({
        kind: "authenticated",
        data: { ...view.data, requests },
        notice: "Decision recorded from current server state.",
      });
    } catch (error) {
      setView({
        kind: "authenticated",
        data: view.data,
        notice:
          error instanceof StaleApprovalError
            ? "Request changed. Reload before deciding."
            : "Decision was rejected by the server.",
      });
    }
  };

  const verifyAudit = async () => {
    if (view.kind !== "authenticated") return;
    try {
      const auditValid = await verifyAuditChain(view.data.identity.organizationId);
      const audit = await loadAuditEvents(view.data.identity.organizationId);
      setView({
        kind: "authenticated",
        data: { ...view.data, audit, auditValid },
        notice: null,
      });
    } catch {
      setView({
        kind: "authenticated",
        data: view.data,
        notice: "Audit verification was rejected by the server.",
      });
    }
  };

  if (view.kind === "authenticated") {
    return (
      <main className="app-shell" aria-labelledby="page-title">
        <DemoConsole
          identity={view.data.identity}
          approvalRoles={view.data.approvalRoles}
          requests={view.data.requests}
          audit={view.data.audit}
          auditValid={view.data.auditValid}
          notice={view.notice}
          onDecide={decide}
          onVerifyAudit={verifyAudit}
          onLogout={logout}
        />
      </main>
    );
  }

  return (
    <main className="auth-shell" aria-labelledby="page-title">
      <section className="auth-hero">
        <div className="environment-badge"><span aria-hidden="true" /> SYNTHETIC LOCAL DEMO</div>
        <p className="eyebrow">W17 / Portfolio Demo Console</p>
        <h1 id="page-title">FlowPilot Arena</h1>
        <p className="lead">
          Local synthetic workflow evidence with database-backed identity, approval, and audit boundaries.
        </p>
      </section>

      {view.kind === "loading" && (
        <section className="auth-card" aria-live="polite">
          <p className="section-kicker">Local identity</p>
          <h2>Checking access</h2>
          <p>Validating the local OIDC transaction and server authorization.</p>
        </section>
      )}

      {view.kind === "signed_out" && (
        <section className="auth-card">
          <p className="section-kicker">Local identity</p>
          <h2>Sign in to the console</h2>
          <p>Use the fixed local Keycloak realm with Authorization Code and PKCE.</p>
          <button type="button" onClick={() => void login()}>Sign in with local OIDC</button>
        </section>
      )}

      {view.kind === "forbidden" && (
        <section className="auth-card is-error" role="alert">
          <p className="section-kicker">Authorization boundary</p>
          <h2>Access forbidden</h2>
          <p>The identity is valid, but its current database membership is not authorized.</p>
          <button type="button" onClick={logout}>Sign out</button>
        </section>
      )}

      {view.kind === "failed" && (
        <section className="auth-card is-error" role="alert">
          <p className="section-kicker">Closed failure</p>
          <h2>Identity check failed</h2>
          <p>The callback, credential exchange, or current identity response was rejected.</p>
          <button type="button" onClick={() => setView({ kind: "signed_out" })}>Return to sign in</button>
        </section>
      )}

      <p className="auth-footnote">
        Credentials stay in memory. Temporary authorization material is never rendered by this console.
      </p>
    </main>
  );
}

export default App;
