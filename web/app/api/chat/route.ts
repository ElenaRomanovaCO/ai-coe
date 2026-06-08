import { type NextRequest } from "next/server";

import { streamChat } from "@/lib/aws";

// Pure streaming passthrough: the browser POSTs a chat turn here, this route signs
// and forwards it to the orchestrator's streaming Function URL, and pipes the SSE
// body straight back with NO buffering. The explicit smoke-test target is that
// tokens stream incrementally in the browser through Amplify SSR — so we never
// await or read the upstream body; we hand its ReadableStream to the Response.

export const dynamic = "force-dynamic"; // never cache; always hit the orchestrator
export const fetchCache = "force-no-store";

export async function POST(req: NextRequest) {
  // /api is excluded from the auth middleware (so /api/login works pre-auth), so
  // gate this billable route on the same auth_ok cookie the rest of the app uses.
  if (req.cookies.get("auth_ok")?.value !== "1") {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "invalid_json" }, { status: 400 });
  }

  const message = typeof body.message === "string" ? body.message.trim() : "";
  const sessionId = typeof body.session_id === "string" ? body.session_id : "";
  if (!message || !sessionId) {
    return Response.json({ error: "message and session_id are required" }, { status: 400 });
  }

  const displayName =
    typeof body.display_name === "string" && body.display_name ? body.display_name : "Guest";
  const currentRoute = typeof body.current_route === "string" ? body.current_route : null;

  const upstream = await streamChat({
    display_name: displayName,
    session_id: sessionId,
    request_id: crypto.randomUUID(),
    message,
    current_route: currentRoute,
  });

  if (!upstream.ok || !upstream.body) {
    return Response.json(
      { error: "orchestrator_error", status: upstream.status },
      { status: 502 },
    );
  }

  // Stream the upstream SSE body through unchanged. Headers discourage any
  // intermediary (Amplify/CloudFront) from buffering the response.
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
