const ACCESS_TOKEN_KEY = "orgflow_access_token";
const ORG_ID_KEY = "orgflow_org_id";

let accessToken: string | null = null;
let orgId: string | null = null;

function readStoredToken(): string | null {
  if (accessToken) {
    return accessToken;
  }

  if (typeof window === "undefined") {
    return null;
  }

  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

function readStoredOrgId(): string | null {
  if (orgId) {
    return orgId;
  }

  if (typeof window === "undefined") {
    return null;
  }

  return sessionStorage.getItem(ORG_ID_KEY);
}

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
}

export function setApiSession(
  token: string,
  organizationId: string
) {
  accessToken = token;
  orgId = organizationId;

  if (typeof window !== "undefined") {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
    sessionStorage.setItem(ORG_ID_KEY, organizationId);
  }
}

export function clearApiSession() {
  accessToken = null;
  orgId = null;

  if (typeof window !== "undefined") {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(ORG_ID_KEY);
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
  userId: string
): Promise<{
  access_token: string;
  org_id: string;
  role: string;
}> {
  const response = await fetch(
    `${getApiBaseUrl()}/auth/exchange`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
      }),
    }
  );

  if (!response.ok) {
    throw new Error("Token exchange failed");
  }

  const data = await response.json();

  setApiSession(
    data.access_token,
    data.org_id
  );

  return data;
}
