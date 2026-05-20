export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const HUB = process.env.ATHOS_HUB_URL ?? "http://localhost:7474";

export async function GET() {
  const token = process.env.ATHOS_TOKEN;
  if (!token) {
    return new Response(
      `data: ${JSON.stringify({ error: "token_missing" })}\n\n`,
      { status: 503, headers: { "Content-Type": "text/event-stream" } }
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${HUB}/api/events`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: "{}",
    });
  } catch {
    return new Response(
      `event: error\ndata: ${JSON.stringify({ error: "hub_unavailable" })}\n\n`,
      { headers: { "Content-Type": "text/event-stream" } }
    );
  }

  if (!upstream.ok || !upstream.body) {
    return new Response(
      `event: error\ndata: ${JSON.stringify({ error: "hub_error", status: upstream.status })}\n\n`,
      { headers: { "Content-Type": "text/event-stream" } }
    );
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
      Connection: "keep-alive",
    },
  });
}
