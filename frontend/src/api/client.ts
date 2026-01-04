const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function postJSON<TRes>(path: string, body: unknown): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = typeof data?.detail === "string" ? data.detail : JSON.stringify(data);
    } catch {
      detail = await res.text().catch(() => "");
    }
    throw new Error(`HTTP ${res.status} - ${detail}`);
  }

  return (await res.json()) as TRes;
}

export async function getJSON<TRes>(path: string): Promise<TRes> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as TRes;
}
