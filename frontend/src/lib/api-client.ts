/**
 * API client utility that attaches Firebase ID token to requests.
 * Use createApiClient(getIdToken) from useAuth() to get an authenticated client.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type TokenGetter = (forceRefresh?: boolean) => Promise<string | null>;

export interface ApiClient {
  /** Fetch from API with Bearer token. Retries once on 401 with refreshed token. */
  fetch<T>(path: string, options?: RequestInit): Promise<T>;
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function parseErrorBody(res: Response): Promise<unknown> {
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  try {
    const text = await res.text();
    return text || null;
  } catch {
    return null;
  }
}

function messageFromErrorBody(status: number, body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === "string") return message;
    }
  }
  if (typeof body === "string" && body.length > 0) return body;
  return `HTTP ${status}`;
}

export function createApiClient(getToken: TokenGetter): ApiClient {
  return {
    async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
      const token = await getToken();
      const headers: HeadersInit = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
        ...(token && { Authorization: `Bearer ${token}` }),
      };

      const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

      if (res.status === 401) {
        const retryToken = await getToken(true);
        if (retryToken) {
          const retryRes = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers: { ...headers, Authorization: `Bearer ${retryToken}` },
          });
          if (!retryRes.ok) {
            const retryBody = await parseErrorBody(retryRes);
            throw new ApiError(
              retryRes.status,
              messageFromErrorBody(retryRes.status, retryBody),
              retryBody
            );
          }
          if (retryRes.status === 204) return undefined as T;
          return retryRes.json();
        }
        throw new ApiError(401, "Unauthorized");
      }

      if (!res.ok) {
        const body = await parseErrorBody(res);
        throw new ApiError(res.status, messageFromErrorBody(res.status, body), body);
      }
      if (res.status === 204) return undefined as T;
      return res.json();
    },
  };
}
