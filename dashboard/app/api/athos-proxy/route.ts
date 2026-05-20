import { NextRequest, NextResponse } from "next/server";

const ATHOS_BASE = process.env.NEXT_PUBLIC_ATHOS_BASE_URL ?? "http://localhost:7474";
const ATHOS_TOKEN = process.env.ATHOS_TOKEN ?? "";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { endpoint, payload = {} } = body as { endpoint: string; payload?: Record<string, unknown> };

  if (!endpoint?.startsWith("/api/")) {
    return NextResponse.json({ error: "invalid endpoint" }, { status: 400 });
  }

  try {
    const res = await fetch(`${ATHOS_BASE}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${ATHOS_TOKEN}`,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 502 });
  }
}
