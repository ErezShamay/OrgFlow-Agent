import { logAuthError, logAuthInfo } from "@/lib/auth/logger";
import {
  ELAYOAI_ACCESS_TOKEN_KEY,
  ELAYOAI_ORG_ID_KEY,
} from "@/lib/elayoai/keys";
import { getApiBaseUrl } from "@/lib/env/public-env";

let accessToken: string | null = null;
let orgId: string | null = null;

function readStoredToken(): string | null {
  if (accessToken) {
    return accessToken;
  }

  if (typeof window === "undefined") {
    return null;
  }

  return sessionStorage.getItem(ELAYOAI_ACCESS_TOKEN_KEY);
}

function readStoredOrgId(): string | null {
  if (orgId) {
    return orgId;
  }

  if (typeof window === "undefined") {
    return null;
  }

  return sessionStorage.getItem(ELAYOAI_ORG_ID_KEY);
}

export { getApiBaseUrl };

export class ProfileLoadError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ProfileLoadError";
    this.status = status;
  }
}

export class TokenExchangeError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "TokenExchangeError";
    this.status = status;
  }
}

export function setApiSession(
  token: string,
  organizationId: string
) {
  accessToken = token;
  orgId = organizationId;

  if (typeof window !== "undefined") {
    sessionStorage.setItem(ELAYOAI_ACCESS_TOKEN_KEY, token);
    sessionStorage.setItem(ELAYOAI_ORG_ID_KEY, organizationId);
  }
}

export function clearApiSession() {
  accessToken = null;
  orgId = null;

  if (typeof window !== "undefined") {
    sessionStorage.removeItem(ELAYOAI_ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(ELAYOAI_ORG_ID_KEY);
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = readStoredToken();
  const organizationId = readStoredOrgId();
  const headers: Record<string, string> = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (organizationId) {
    headers["X-Organization-ID"] = organizationId;
  }

  return headers;
}

function getAlternateApiUrl(url: string): string {
  if (url.includes("127.0.0.1")) {
    return url.replace("127.0.0.1", "localhost");
  }

  if (url.includes("localhost")) {
    return url.replace("localhost", "127.0.0.1");
  }

  return url;
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const url = path.startsWith("http")
    ? path
    : `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers);
  const authHeaders = getAuthHeaders();

  Object.entries(authHeaders).forEach(([key, value]) => {
    headers.set(key, value);
  });

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  try {
    return await fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    const altUrl = getAlternateApiUrl(url);

    if (altUrl === url) {
      throw error;
    }

    return fetch(altUrl, {
      ...options,
      headers,
    });
  }
}

export async function exchangeBackendToken(
  userId: string,
  organizationId?: string | null
): Promise<{
  access_token: string;
  org_id: string;
  role: string;
}> {
  const baseUrl = getApiBaseUrl();
  const urls = [
    `${baseUrl}/auth/exchange`,
    `${getAlternateApiUrl(baseUrl)}/auth/exchange`,
  ];
  const uniqueUrls = [...new Set(urls)];

  let response: Response | null = null;

  logAuthInfo("token_exchange:start", {
    userId,
    organizationId: organizationId ?? null,
    apiBaseUrl: baseUrl,
    urls: uniqueUrls,
  });

  let lastNetworkError: unknown = null;

  for (const url of uniqueUrls) {
    try {
      response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          ...(organizationId
            ? { organization_id: organizationId }
            : {}),
        }),
      });
      break;
    } catch (error) {
      lastNetworkError = error;
      logAuthError("token_exchange:network", error, { url });

      if (url === uniqueUrls[uniqueUrls.length - 1]) {
        throw error;
      }
    }
  }

  if (!response) {
    logAuthError("token_exchange:no_response", lastNetworkError, {
      userId,
      apiBaseUrl: baseUrl,
    });
    throw new TokenExchangeError(
      "Token exchange failed - no response from API",
      0
    );
  }

  if (!response.ok) {
    let message = "Token exchange failed";

    try {
      const body = await response.json();
      message =
        body?.detail
        || body?.error?.message
        || message;
    } catch {
      // Keep default message when error body is not JSON.
    }

    logAuthError("token_exchange:http", new Error(message), {
      userId,
      status: response.status,
      url: response.url,
    });

    throw new TokenExchangeError(
      message,
      response.status
    );
  }

  const data = await response.json();

  setApiSession(
    data.access_token,
    data.org_id
  );

  logAuthInfo("token_exchange:ok", {
    userId,
    orgId: data.org_id,
    role: data.role,
  });

  return data;
}
