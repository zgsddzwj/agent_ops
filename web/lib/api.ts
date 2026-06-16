const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Custom API error with status code and detail */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail?: string
  ) {
    super(`API error ${status}: ${statusText}${detail ? ` - ${detail}` : ""}`);
    this.name = "ApiError";
  }
}

export async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
  apiKey?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (apiKey) headers["X-API-Key"] = apiKey;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      cache: "no-store",
      signal: controller.signal,
    });

    if (!res.ok) {
      let detail: string | undefined;
      try {
        const body = await res.json();
        detail = body.detail || body.message;
      } catch {
        // Response body is not JSON
      }
      throw new ApiError(res.status, res.statusText, detail);
    }

    return res.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(408, "Request Timeout", "The request was aborted due to timeout");
    }
    if (err instanceof TypeError) {
      throw new ApiError(0, "Network Error", "Unable to connect to the API server");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export { API_URL };
