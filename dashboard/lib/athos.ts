const BASE = process.env.NEXT_PUBLIC_ATHOS_BASE_URL ?? "http://localhost:7474";
const TOKEN = process.env.ATHOS_TOKEN ?? "";

export function athosHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${TOKEN}`,
  };
}

export async function athosPost<T = unknown>(
  path: string,
  body: Record<string, unknown> = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: athosHeaders(),
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`ATHOS ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export async function athosGet<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: athosHeaders(),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`ATHOS GET ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const ATHOS_BASE = BASE;
export const ATHOS_TOKEN = TOKEN;
