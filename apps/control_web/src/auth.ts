const OIDC_ISSUER = "http://127.0.0.1:8080/realms/flowpilot";
const AUTHORIZATION_ENDPOINT = `${OIDC_ISSUER}/protocol/openid-connect/auth`;
const TOKEN_ENDPOINT = `${OIDC_ISSUER}/protocol/openid-connect/token`;
const LOGOUT_ENDPOINT = `${OIDC_ISSUER}/protocol/openid-connect/logout`;
const CLIENT_ID = "flowpilot-control-web";
const REDIRECT_URI = "http://127.0.0.1:5173/callback";
const POST_LOGOUT_URI = "http://127.0.0.1:5173/";
const CONTROL_API_ORIGIN = "http://127.0.0.1:8000";
const CONTROL_WEB_ORIGIN = "http://127.0.0.1:5173";
const TRANSACTION_KEY = "flowpilot.w10.oidc.transaction";
const TRANSACTION_MAX_AGE_MS = 5 * 60 * 1000;

let accessToken: string | null = null;

type AuthTransaction = Readonly<{
  verifier: string;
  state: string;
  nonce: string;
  createdAt: number;
}>;

export type CurrentIdentity = Readonly<{
  userId: string;
  organizationId: string;
  membershipId: string;
  role: "organization_admin" | "operator" | "auditor";
  permissions: readonly string[];
  authorizationHash: string;
}>;

export class ForbiddenError extends Error {}

const base64Url = (bytes: Uint8Array): string => {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
};

const randomValue = (cryptoProvider: Crypto): string => {
  const bytes = new Uint8Array(32);
  cryptoProvider.getRandomValues(bytes);
  return base64Url(bytes);
};

const sha256 = async (value: string, cryptoProvider: Crypto): Promise<string> => {
  const digest = await cryptoProvider.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return base64Url(new Uint8Array(digest));
};

const exactKeys = (value: Record<string, unknown>, expected: readonly string[]): boolean => {
  const actual = Object.keys(value).sort();
  const required = [...expected].sort();
  return actual.length === required.length && actual.every((item, index) => item === required[index]);
};

const readTransaction = (storage: Storage, now: number): AuthTransaction => {
  const raw = storage.getItem(TRANSACTION_KEY);
  storage.removeItem(TRANSACTION_KEY);
  if (raw === null || raw.length > 2048) {
    throw new Error("OIDC transaction is missing");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("OIDC transaction is invalid");
  }
  if (
    typeof parsed !== "object" ||
    parsed === null ||
    !exactKeys(parsed as Record<string, unknown>, ["verifier", "state", "nonce", "createdAt"])
  ) {
    throw new Error("OIDC transaction is invalid");
  }
  const candidate = parsed as Record<string, unknown>;
  if (
    typeof candidate.verifier !== "string" ||
    typeof candidate.state !== "string" ||
    typeof candidate.nonce !== "string" ||
    typeof candidate.createdAt !== "number" ||
    !/^[A-Za-z0-9_-]{43}$/u.test(candidate.verifier) ||
    !/^[A-Za-z0-9_-]{43}$/u.test(candidate.state) ||
    !/^[A-Za-z0-9_-]{43}$/u.test(candidate.nonce) ||
    !Number.isSafeInteger(candidate.createdAt) ||
    candidate.createdAt > now ||
    now - candidate.createdAt > TRANSACTION_MAX_AGE_MS
  ) {
    throw new Error("OIDC transaction is invalid");
  }
  return {
    verifier: candidate.verifier,
    state: candidate.state,
    nonce: candidate.nonce,
    createdAt: candidate.createdAt,
  };
};

const requireExactOrigin = (origin: string): void => {
  if (origin !== CONTROL_WEB_ORIGIN) {
    throw new Error("Control Web origin is not allowlisted");
  }
};

export const prepareLogin = async (
  storage: Storage = window.sessionStorage,
  cryptoProvider: Crypto = window.crypto,
  now: number = Date.now(),
): Promise<string> => {
  requireExactOrigin(window.location.origin);
  const transaction: AuthTransaction = {
    verifier: randomValue(cryptoProvider),
    state: randomValue(cryptoProvider),
    nonce: randomValue(cryptoProvider),
    createdAt: now,
  };
  const challenge = await sha256(transaction.verifier, cryptoProvider);
  storage.setItem(TRANSACTION_KEY, JSON.stringify(transaction));
  const url = new URL(AUTHORIZATION_ENDPOINT);
  url.searchParams.set("client_id", CLIENT_ID);
  url.searchParams.set("redirect_uri", REDIRECT_URI);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid");
  url.searchParams.set("code_challenge", challenge);
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("state", transaction.state);
  url.searchParams.set("nonce", transaction.nonce);
  return url.toString();
};

const singleParameter = (url: URL, name: string): string => {
  const values = url.searchParams.getAll(name);
  if (values.length !== 1 || values[0] === "") {
    throw new Error("OIDC callback parameter is invalid");
  }
  return values[0];
};

const decodeJwtPayload = (token: string): Record<string, unknown> => {
  const parts = token.split(".");
  if (parts.length !== 3 || parts.some((part) => part.length === 0)) {
    throw new Error("ID token is malformed");
  }
  const padded = parts[1].replaceAll("-", "+").replaceAll("_", "/").padEnd(
    Math.ceil(parts[1].length / 4) * 4,
    "=",
  );
  let payload: unknown;
  try {
    payload = JSON.parse(atob(padded));
  } catch {
    throw new Error("ID token is malformed");
  }
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
    throw new Error("ID token is malformed");
  }
  return payload as Record<string, unknown>;
};

const validateIdToken = (token: string, nonce: string, now: number): void => {
  const payload = decodeJwtPayload(token);
  const audience = payload.aud;
  const audienceMatches =
    audience === CLIENT_ID ||
    (Array.isArray(audience) && audience.length > 0 && audience.every((item) => typeof item === "string") && audience.includes(CLIENT_ID));
  if (
    payload.iss !== OIDC_ISSUER ||
    !audienceMatches ||
    payload.azp !== CLIENT_ID ||
    payload.nonce !== nonce ||
    typeof payload.exp !== "number" ||
    !Number.isSafeInteger(payload.exp) ||
    payload.exp * 1000 <= now
  ) {
    throw new Error("ID token claims are invalid");
  }
};

export const handleCallback = async (
  callbackUrl: string = window.location.href,
  storage: Storage = window.sessionStorage,
  fetcher: typeof fetch = window.fetch.bind(window),
  now: number = Date.now(),
): Promise<void> => {
  const url = new URL(callbackUrl);
  requireExactOrigin(url.origin);
  if (url.pathname !== "/callback" || url.hash !== "" || url.searchParams.has("error")) {
    storage.removeItem(TRANSACTION_KEY);
    throw new Error("OIDC callback is rejected");
  }
  const allowed = new Set(["code", "state", "session_state", "iss"]);
  if ([...url.searchParams.keys()].some((name) => !allowed.has(name))) {
    storage.removeItem(TRANSACTION_KEY);
    throw new Error("OIDC callback is rejected");
  }
  const transaction = readTransaction(storage, now);
  const state = singleParameter(url, "state");
  const code = singleParameter(url, "code");
  const returnedIssuer = url.searchParams.get("iss");
  if (state !== transaction.state || (returnedIssuer !== null && returnedIssuer !== OIDC_ISSUER)) {
    throw new Error("OIDC callback state or issuer is invalid");
  }
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    code,
    code_verifier: transaction.verifier,
  });
  const response = await fetcher(TOKEN_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    redirect: "error",
    credentials: "omit",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("OIDC token exchange failed");
  }
  const result: unknown = await response.json();
  if (typeof result !== "object" || result === null || Array.isArray(result)) {
    throw new Error("OIDC token response is invalid");
  }
  const tokenResponse = result as Record<string, unknown>;
  if (
    typeof tokenResponse.access_token !== "string" ||
    typeof tokenResponse.id_token !== "string" ||
    tokenResponse.token_type !== "Bearer" ||
    typeof tokenResponse.expires_in !== "number" ||
    tokenResponse.expires_in <= 0
  ) {
    throw new Error("OIDC token response is invalid");
  }
  validateIdToken(tokenResponse.id_token, transaction.nonce, now);
  accessToken = tokenResponse.access_token;
};

const parseCurrentIdentity = (value: unknown): CurrentIdentity => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("Current identity response is invalid");
  }
  const item = value as Record<string, unknown>;
  const expected = [
    "schema_version",
    "user_id",
    "organization_id",
    "membership_id",
    "role",
    "permissions",
    "authorization_hash",
  ];
  const roles = new Set(["organization_admin", "operator", "auditor"]);
  if (
    !exactKeys(item, expected) ||
    item.schema_version !== "w10-current-identity/1.0" ||
    typeof item.user_id !== "string" ||
    typeof item.organization_id !== "string" ||
    typeof item.membership_id !== "string" ||
    typeof item.role !== "string" ||
    !roles.has(item.role) ||
    !Array.isArray(item.permissions) ||
    !item.permissions.every((permission) => typeof permission === "string") ||
    typeof item.authorization_hash !== "string" ||
    !/^[0-9a-f]{64}$/u.test(item.authorization_hash)
  ) {
    throw new Error("Current identity response is invalid");
  }
  return {
    userId: item.user_id,
    organizationId: item.organization_id,
    membershipId: item.membership_id,
    role: item.role as CurrentIdentity["role"],
    permissions: item.permissions,
    authorizationHash: item.authorization_hash,
  };
};

export const loadCurrentIdentity = async (
  fetcher: typeof fetch = window.fetch.bind(window),
): Promise<CurrentIdentity> => {
  if (accessToken === null) {
    throw new Error("No in-memory access token");
  }
  const response = await fetcher(`${CONTROL_API_ORIGIN}/api/v1/identity/me`, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
    credentials: "omit",
    cache: "no-store",
    redirect: "error",
  });
  if (response.status === 403) {
    throw new ForbiddenError("Identity is authenticated but not authorized");
  }
  if (!response.ok) {
    accessToken = null;
    throw new Error("Current identity request failed");
  }
  return parseCurrentIdentity(await response.json());
};

export const authorizedApiFetch = async (
  path: string,
  init: RequestInit = {},
  fetcher: typeof fetch = window.fetch.bind(window),
): Promise<Response> => {
  const method = (init.method ?? "GET").toUpperCase();
  const routes: readonly Readonly<{ pattern: RegExp; method: "GET" | "POST" }>[] = [
    { pattern: /^\/api\/v1\/approval-authorities\/me$/u, method: "GET" },
    {
      pattern: /^\/api\/v1\/organizations\/org_[A-Za-z0-9_-]{8,64}\/approval-requests$/u,
      method: "GET",
    },
    {
      pattern:
        /^\/api\/v1\/organizations\/org_[A-Za-z0-9_-]{8,64}\/approval-requests\/apr_[A-Za-z0-9_-]{8,64}$/u,
      method: "GET",
    },
    {
      pattern:
        /^\/api\/v1\/organizations\/org_[A-Za-z0-9_-]{8,64}\/approval-requests\/apr_[A-Za-z0-9_-]{8,64}\/decisions$/u,
      method: "POST",
    },
    {
      pattern: /^\/api\/v1\/organizations\/org_[A-Za-z0-9_-]{8,64}\/audit-events$/u,
      method: "GET",
    },
    {
      pattern:
        /^\/api\/v1\/organizations\/org_[A-Za-z0-9_-]{8,64}\/audit-events\/verify$/u,
      method: "POST",
    },
  ];
  if (
    path.includes("?") ||
    path.includes("#") ||
    !routes.some((route) => route.method === method && route.pattern.test(path))
  ) {
    throw new Error("Control API path is outside the closed allowlist");
  }
  const url = new URL(path, CONTROL_API_ORIGIN);
  if (url.origin !== CONTROL_API_ORIGIN) {
    throw new Error("Control API origin is outside the closed allowlist");
  }
  if (accessToken === null) {
    throw new Error("No in-memory access token");
  }
  const headers = new Headers(init.headers);
  if (headers.has("Authorization")) {
    throw new Error("Caller-provided Authorization is forbidden");
  }
  headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetcher(url.toString(), {
    ...init,
    headers,
    credentials: "omit",
    cache: "no-store",
    redirect: "error",
  });
  if (response.status === 403) {
    throw new ForbiddenError("Identity is authenticated but not authorized");
  }
  if (response.status === 401) {
    accessToken = null;
  }
  return response;
};

export const logoutUrl = (storage: Storage = window.sessionStorage): string => {
  accessToken = null;
  storage.removeItem(TRANSACTION_KEY);
  const url = new URL(LOGOUT_ENDPOINT);
  url.searchParams.set("client_id", CLIENT_ID);
  url.searchParams.set("post_logout_redirect_uri", POST_LOGOUT_URI);
  return url.toString();
};

export const hasInMemoryToken = (): boolean => accessToken !== null;

export const clearInMemoryAuth = (storage: Storage = window.sessionStorage): void => {
  accessToken = null;
  storage.removeItem(TRANSACTION_KEY);
};
