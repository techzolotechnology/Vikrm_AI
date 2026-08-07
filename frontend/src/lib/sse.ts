import { useAuthStore } from "@/store/use-auth-store";

interface StreamEvent {
  delta?: string;
  error?: string;
  done?: boolean;
  title?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/**
 * POSTs to an SSE endpoint and yields parsed events as they arrive.
 *
 * Performance notes:
 * - Uses raw `fetch` with ReadableStream (Axios doesn't support chunked streaming)
 * - Bearer token attached manually
 * - Retries once on 401 with a silent token refresh
 * - Graceful reader.read() error handling (server-side stream close)
 */
export async function* streamSSE(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const doFetch = (token: string | null) =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
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
    let errorText = `Request failed with status ${response.status}`;
    try {
      const errData = await response.json();
      if (errData?.detail) {
        errorText =
          typeof errData.detail === "string"
            ? errData.detail
            : JSON.stringify(errData.detail);
      }
    } catch {
      // ignore parse error
    }
    throw new Error(errorText);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      let done = false;
      let value: Uint8Array | undefined;
      try {
        const result = await reader.read();
        done = result.done;
        value = result.value;
      } catch {
        // Stream reading interrupted or aborted
        break;
      }
      if (done || !value) break;

      buffer += decoder.decode(value, { stream: true });

      // Split on double-newline (SSE frame boundary)
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const frame of frames) {
        for (const line of frame.split("\n")) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.slice("data:".length).trim();
          if (!jsonStr) continue;
          if (jsonStr === "[DONE]") {
            yield { done: true };
            return;
          }
          try {
            const event = JSON.parse(jsonStr) as StreamEvent;
            yield event;
            if (event.done) return;
          } catch {
            // Ignore malformed keep-alive/partial frames
          }
        }
      }
    }

    // Flush any remaining buffer content
    if (buffer.trim()) {
      for (const line of buffer.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const jsonStr = trimmed.slice("data:".length).trim();
        if (!jsonStr) continue;
        if (jsonStr === "[DONE]") {
          yield { done: true };
          return;
        }
        try {
          yield JSON.parse(jsonStr) as StreamEvent;
        } catch {
          // ignore
        }
      }
    }
  } finally {
    try {
      await reader.cancel().catch(() => {});
      reader.releaseLock();
    } catch {
      // ignore releaseLock error if stream was closed
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
