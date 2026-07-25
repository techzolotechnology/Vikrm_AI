import { useAuthStore } from "@/store/use-auth-store";

interface StreamEvent {
  delta?: string;
  error?: string;
  done?: boolean;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/**
 * POSTs to an SSE endpoint and yields parsed events as they arrive.
 * Uses raw `fetch` (not axios) since axios doesn't support incremental
 * ReadableStream consumption. Attaches the bearer token manually and
 * retries exactly once after a silent token refresh on 401, mirroring
 * the axios interceptor's behavior for regular requests.
 */
export async function* streamSSE(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const doFetch = async (token: string | null) =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal,
    });

  let response = await doFetch(useAuthStore.getState().accessToken);

  if (response.status === 401) {
    const refreshed = await tryRefresh();
    if (!refreshed) {
      throw new Error("Session expired. Please sign in again.");
    }
    response = await doFetch(useAuthStore.getState().accessToken);
  }

  if (!response.ok || !response.body) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const jsonStr = trimmed.slice("data:".length).trim();
      try {
        yield JSON.parse(jsonStr) as StreamEvent;
      } catch {
        // Ignore malformed keep-alive/partial lines rather than crashing the stream.
      }
    }
  }
}

async function tryRefresh(): Promise<boolean> {
  const { refreshToken, user, setSession } = useAuthStore.getState();
  if (!refreshToken || !user) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) return false;

    const data = (await response.json()) as { access_token: string; refresh_token: string };
    setSession({ accessToken: data.access_token, refreshToken: data.refresh_token, user });
    return true;
  } catch {
    return false;
  }
}
