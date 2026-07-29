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

  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">W11 / Approval boundary</p>
        <h1 id="page-title">FlowPilot Arena</h1>
        <p className="lead">
          Database-backed identity, closed risk policy, one-time approval, and tamper-evident audit.
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
        <>
          <section className="card" aria-labelledby="identity-title">
            <h2 id="identity-title">Current identity</h2>
            <dl>
              <div>
                <dt>Organization</dt>
                <dd>{view.data.identity.organizationId}</dd>
              </div>
              <div>
                <dt>Business role</dt>
                <dd>{view.data.identity.role}</dd>
              </div>
              <div>
                <dt>Approval role</dt>
                <dd>{view.data.approvalRoles.join(", ") || "none"}</dd>
              </div>
            </dl>
            <button type="button" onClick={logout}>
              Sign out
            </button>
          </section>

          <section className="card" aria-labelledby="approval-title">
            <h2 id="approval-title">Approval requests</h2>
            {view.data.requests.length === 0 ? (
              <p>No organization approval requests.</p>
            ) : (
              <ul className="request-list">
                {view.data.requests.map((item) => (
                  <li key={item.requestId}>
                    <div>
                      <strong>{item.actionType}</strong>
                      <span>
                        {item.riskLevel} / {item.status}
                      </span>
                      <span>
                        Task {item.taskId} / step {item.stepId}
                      </span>
                      <span>Binding {item.parameterHash}</span>
                      <span>Expires {item.expiresAt}</span>
                    </div>
                    {item.status === "pending" && view.data.approvalRoles.length > 0 && (
                      <div className="button-row">
                        <button type="button" onClick={() => void decide(item.requestId, "approved")}>
                          Approve
                        </button>
                        <button type="button" onClick={() => void decide(item.requestId, "rejected")}>
                          Reject
                        </button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {view.notice !== null && <p role="status">{view.notice}</p>}
          </section>

          {view.data.identity.permissions.includes("audit.read") && (
            <section className="card" aria-labelledby="audit-title">
              <h2 id="audit-title">Audit chain</h2>
              <p>{view.data.audit.events.length} append-only event references.</p>
              <p>
                Head {view.data.audit.headSequence} / {view.data.audit.headHash}
              </p>
              {view.data.audit.events.length > 0 && (
                <ol className="audit-list">
                  {view.data.audit.events.map((event) => (
                    <li key={event.eventId}>
                      <span>#{event.sequence}</span>
                      <strong>{event.eventType}</strong>
                      <span>{event.eventHash}</span>
                    </li>
                  ))}
                </ol>
              )}
              <p>
                Verification: {view.data.auditValid === null ? "not run" : view.data.auditValid ? "valid" : "failed"}
              </p>
              {view.data.identity.permissions.includes("audit.verify") && (
                <button type="button" onClick={() => void verifyAudit()}>
                  Verify audit chain
                </button>
              )}
            </section>
          )}
        </>
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
        Tokens stay in memory. Approval grants and nonce material never enter the browser.
      </p>
    </main>
  );
}

export default App;
