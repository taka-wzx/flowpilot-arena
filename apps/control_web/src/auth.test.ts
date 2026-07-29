import { webcrypto } from "node:crypto";

import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearInMemoryAuth,
  handleCallback,
  hasInMemoryToken,
  loadCurrentIdentity,
  logoutUrl,
  prepareLogin,
} from "./auth";

const cryptoProvider = webcrypto as Crypto;

const jwt = (payload: Record<string, unknown>): string => {
  const encode = (value: object) =>
    btoa(JSON.stringify(value)).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
  return `${encode({ alg: "RS256", typ: "JWT" })}.${encode(payload)}.runtime-signature`;
};

describe("W10 browser OIDC", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    window.sessionStorage.clear();
    window.localStorage.clear();
    clearInMemoryAuth();
  });

  it("prepares exact Authorization Code + S256 PKCE, state, and nonce", async () => {
    const url = new URL(await prepareLogin(window.sessionStorage, cryptoProvider, 1000));
    const transaction = JSON.parse(
      window.sessionStorage.getItem("flowpilot.w10.oidc.transaction") ?? "null",
    ) as Record<string, unknown>;

    expect(url.origin).toBe("http://127.0.0.1:8080");
    expect(url.pathname).toBe("/realms/flowpilot/protocol/openid-connect/auth");
    expect(url.searchParams.get("client_id")).toBe("flowpilot-control-web");
    expect(url.searchParams.get("redirect_uri")).toBe("http://127.0.0.1:5173/callback");
    expect(url.searchParams.get("response_type")).toBe("code");
    expect(url.searchParams.get("code_challenge_method")).toBe("S256");
    expect(url.searchParams.get("state")).toBe(transaction.state);
    expect(url.searchParams.get("nonce")).toBe(transaction.nonce);
    expect(JSON.stringify(transaction).toLowerCase()).not.toContain("token");
    expect(window.localStorage.length).toBe(0);
  });

  it("validates callback state and nonce, keeps access token only in memory, and loads identity", async () => {
    await prepareLogin(window.sessionStorage, cryptoProvider, 1000);
    const transaction = JSON.parse(
      window.sessionStorage.getItem("flowpilot.w10.oidc.transaction") ?? "null",
    ) as { state: string; nonce: string };
    const idToken = jwt({
      iss: "http://127.0.0.1:8080/realms/flowpilot",
      aud: "flowpilot-control-web",
      azp: "flowpilot-control-web",
      nonce: transaction.nonce,
      exp: 100,
    });
    const tokenFetch = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "runtime-access-token",
          id_token: idToken,
          token_type: "Bearer",
          expires_in: 300,
          refresh_token: "ignored-runtime-refresh-token",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await handleCallback(
      `http://127.0.0.1:5173/callback?code=runtime-code&state=${transaction.state}`,
      window.sessionStorage,
      tokenFetch,
      2000,
    );

    expect(hasInMemoryToken()).toBe(true);
    expect(window.sessionStorage.length).toBe(0);
    expect(window.localStorage.length).toBe(0);
    const identityFetch = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          schema_version: "w10-current-identity/1.0",
          user_id: "usr_syn_alpha_admin_0001",
          organization_id: "org_syn_alpha_0001",
          membership_id: "mbr_syn_alpha_admin_0001",
          role: "organization_admin",
          permissions: ["organization.read"],
          authorization_hash: "a".repeat(64),
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    const identity = await loadCurrentIdentity(identityFetch);

    expect(identity.organizationId).toBe("org_syn_alpha_0001");
    const authorization = (identityFetch.mock.calls[0]?.[1]?.headers as Record<string, string>)
      .Authorization;
    expect(authorization).toBe("Bearer runtime-access-token");
    expect(window.localStorage.length).toBe(0);
  });

  it("rejects state and nonce mismatch before retaining authentication", async () => {
    await prepareLogin(window.sessionStorage, cryptoProvider, 1000);
    const wrongStateFetch = vi.fn<typeof fetch>();
    await expect(
      handleCallback(
        "http://127.0.0.1:5173/callback?code=runtime-code&state=wrong-state",
        window.sessionStorage,
        wrongStateFetch,
        2000,
      ),
    ).rejects.toThrow(/state/iu);
    expect(wrongStateFetch).not.toHaveBeenCalled();
    expect(hasInMemoryToken()).toBe(false);

    await prepareLogin(window.sessionStorage, cryptoProvider, 3000);
    const transaction = JSON.parse(
      window.sessionStorage.getItem("flowpilot.w10.oidc.transaction") ?? "null",
    ) as { state: string };
    const nonceFetch = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          access_token: "must-not-be-retained",
          id_token: jwt({
            iss: "http://127.0.0.1:8080/realms/flowpilot",
            aud: "flowpilot-control-web",
            azp: "flowpilot-control-web",
            nonce: "wrong-nonce",
            exp: 100,
          }),
          token_type: "Bearer",
          expires_in: 300,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    await expect(
      handleCallback(
        `http://127.0.0.1:5173/callback?code=runtime-code&state=${transaction.state}`,
        window.sessionStorage,
        nonceFetch,
        4000,
      ),
    ).rejects.toThrow(/claims/iu);
    expect(hasInMemoryToken()).toBe(false);
  });

  it("builds an exact post-logout URL without token material", () => {
    const url = new URL(logoutUrl());

    expect(url.origin).toBe("http://127.0.0.1:8080");
    expect(url.searchParams.get("client_id")).toBe("flowpilot-control-web");
    expect(url.searchParams.get("post_logout_redirect_uri")).toBe(
      "http://127.0.0.1:5173/",
    );
    expect(url.toString().toLowerCase()).not.toContain("token");
  });
});
