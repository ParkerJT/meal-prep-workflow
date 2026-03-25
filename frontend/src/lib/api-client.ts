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
          if (!retryRes.ok) throw new Error(`HTTP ${retryRes.status}`);
          if (retryRes.status === 204) return undefined as T;
          return retryRes.json();
        }
        throw new Error("Unauthorized");
      }

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (res.status === 204) return undefined as T;
      return res.json();
    },
  };
}
