// =============================================================================
// MediVault AI — Centralized API Configuration
//
// SETUP (required before running on any remote device):
//   1. Create .env.local (or .env) in the project root
//   2. Add:  VITE_API_BASE_URL=https://<your-tunnel>.ngrok-free.app
//      (copy the exact HTTPS URL printed by ./scripts/start_with_tunnel.sh)
//   3. NEVER use localhost, 127.0.0.1, or 192.168.29.95 here.
//   4. Restart the dev server — all calls auto-route to the new URL.
//
// To migrate tunnel URL:  update VITE_API_BASE_URL, restart.  Zero refactor.
// To go to production:    VITE_API_BASE_URL=https://api.medivault.ai
// =============================================================================

// Support both Vite (`VITE_API_BASE_URL`) and Next.js/CRA (`NEXT_PUBLIC_API_BASE_URL`) env names.
export const BASE_URL: string =
  (import.meta as any).env?.VITE_API_BASE_URL ??
  (import.meta as any).env?.NEXT_PUBLIC_API_BASE_URL ??
  "";

// ---------------------------------------------------------------------------
// ngrok free tier: every request MUST carry this header or ngrok returns an
// HTML warning page instead of the JSON API response.
// ---------------------------------------------------------------------------
const NGROK_HEADER = { "ngrok-skip-browser-warning": "true" } as const;

// ---------------------------------------------------------------------------
// Token storage — access token is tab-scoped (sessionStorage),
// refresh token survives tab close (localStorage).
// ---------------------------------------------------------------------------
export const tokenStore = {
  getAccess:  () => sessionStorage.getItem("mv_access") ?? "",
  getRefresh: () => localStorage.getItem("mv_refresh") ?? "",
  set: (access: string, refresh: string) => {
    // keep storage usage consistent; use sessionStorage for access token
    sessionStorage.setItem("mv_access", access);
    // refresh token must be stored for refresh flows; keep it in localStorage
    localStorage.setItem("mv_refresh", refresh);
  },
  clear: () => {
    sessionStorage.removeItem("mv_access");
    localStorage.removeItem("mv_refresh");
  },
};

// ---------------------------------------------------------------------------
// Default headers for JSON requests
// ---------------------------------------------------------------------------
export function defaultHeaders(token?: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...NGROK_HEADER,
    ...(token ?? tokenStore.getAccess()
      ? { Authorization: `Bearer ${token ?? tokenStore.getAccess()}` }
      : {}),
  };
}

// ---------------------------------------------------------------------------
// Upload headers (multipart — browser sets Content-Type + boundary automatically)
// ---------------------------------------------------------------------------
export function uploadHeaders(token?: string): HeadersInit {
  return {
    ...NGROK_HEADER,
    ...(token ?? tokenStore.getAccess()
      ? { Authorization: `Bearer ${token ?? tokenStore.getAccess()}` }
      : {}),
  };
}

// ---------------------------------------------------------------------------
// Token refresh — called automatically on 401
// ---------------------------------------------------------------------------
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const res = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...NGROK_HEADER },
      body: JSON.stringify({ refresh_token: tokenStore.getRefresh() }),
    });
    if (!res.ok) {
      tokenStore.clear();
      throw new Error("Session expired — please sign in again.");
    }
    const data = await res.json();
    tokenStore.set(data.access_token, data.refresh_token ?? tokenStore.getRefresh());
    refreshPromise = null;
    return data.access_token as string;
  })();
  return refreshPromise;
}

// ---------------------------------------------------------------------------
// Core fetch helper — auto-retries once after token refresh on 401
// ---------------------------------------------------------------------------
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
  isRetry = false
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...defaultHeaders(), ...options.headers },
  });

  if (res.status === 401 && !isRetry) {
    const newToken = await refreshAccessToken();
    return apiFetch<T>(path, {
      ...options,
      headers: { ...defaultHeaders(newToken), ...options.headers },
    }, true);
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Multipart upload helper (records, blood reports, journal audio)
// ---------------------------------------------------------------------------
export async function apiUpload<T = unknown>(
  path: string,
  formData: FormData,
  isRetry = false
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: uploadHeaders(),
    body: formData,
  });

  if (res.status === 401 && !isRetry) {
    const newToken = await refreshAccessToken();
    return apiUpload<T>(path, formData, true);
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Upload ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// SSE streaming helper for AI chat
// POST /api/v1/ai/chat  →  text/event-stream
// Event shapes:
//   { "type": "start" }
//   { "type": "token", "content": "..." }
//   { "type": "done" }
//
// Usage:
//   const stop = streamChat("Tell me about my HbA1c", (token) => append(token), onDone);
//   stop();  // call to abort
// ---------------------------------------------------------------------------
export function streamChat(
  message: string,
  onToken: (chunk: string) => void,
  onDone: () => void,
  onError?: (err: string) => void
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/ai/chat`, {
        method: "POST",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...NGROK_HEADER,
          Authorization: `Bearer ${tokenStore.getAccess()}`,
        },
        body: JSON.stringify({ message }),
      });

      if (!res.ok) {
        onError?.(`Chat API error ${res.status}`);
        return;
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) { onDone(); return; }

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const payload = trimmed.slice(5).trim();
          if (payload === "[DONE]") { onDone(); return; }
          try {
            const evt = JSON.parse(payload);
            if (evt.type === "token" && evt.content) onToken(evt.content);
            if (evt.type === "done") { onDone(); return; }
          } catch {
            // non-JSON line — ignore
          }
        }
      }
      onDone();
    } catch (err: any) {
      if (err?.name !== "AbortError") onError?.(err?.message ?? "Stream error");
    }
  })();

  return () => controller.abort();
}

// ---------------------------------------------------------------------------
// All API endpoint paths (consume BASE_URL — never hardcode URLs in components)
// ---------------------------------------------------------------------------
export const API = {
  auth: {
    register: "/api/v1/auth/register",
    login:    "/api/v1/auth/login",
    refresh:  "/api/v1/auth/refresh",
    logout:   "/api/v1/auth/logout",
  },
  records: {
    upload: "/api/v1/records/upload",
    list:   "/api/v1/records",
  },
  blood: {
    analyze: "/api/v1/blood/analyze",
    history: "/api/v1/blood/history",
  },
  journal: {
    transcribe: "/api/v1/journal/transcribe",
    create:     "/api/v1/journal/create",
    history:    "/api/v1/journal/history",
  },
  timeline: {
    feed: "/api/v1/timeline/get_chronological_feed",
  },
  ai: {
    chat: "/api/v1/ai/chat",
  },
  insights: {
    symptoms:   "/api/v1/insights/get_symptom_trends",
    compliance: "/api/v1/insights/get_compliance_metrics",
  },
  medications: {
    base: "/api/v1/medications",
  },
  doctors: {
    query:        "/api/v1/doctors/query_directory",
    book:         "/api/v1/doctors/book_appointment",
    appointments: "/api/v1/doctors/list_appointments",
  },
  family: {
    manage:   "/api/v1/family/manage_members",
    profiles: "/api/v1/family/fetch_profiles",
  },
  wearables: {
    sync:    "/api/v1/wearables/sync_telemetry",
    metrics: "/api/v1/wearables/get_historical_metrics",
  },
  emergency: {
    fetch:    "/api/v1/emergency-card/fetch",
    generate: "/api/v1/emergency-card/generate_metadata",
  },
  system: {
    health:    "/api/v1/system/health",
    tunnelUrl: "/api/v1/system/tunnel-url",
  },
} as const;
