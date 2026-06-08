// Minimal Server-Sent Events parser for a fetch Response body. The orchestrator
// emits frames of the form:
//
//   event: token\ndata: {"text":"..."}\n\n
//
// (event types: token | tool | citation | done | error). This yields one parsed
// {event, data} per frame as bytes arrive, so the UI can render token-by-token.

export interface SSEEvent {
  event: string;
  data: unknown;
}

function parseFrame(raw: string): SSEEvent | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith(":")) continue; // comment / keep-alive
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).replace(/^ /, ""));
    }
  }
  if (dataLines.length === 0) return null;
  const payload = dataLines.join("\n");
  try {
    return { event, data: JSON.parse(payload) };
  } catch {
    return { event, data: payload };
  }
}

/** Parse an SSE stream into events. Stops when the stream closes or is aborted. */
export async function* parseSSE(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buf.indexOf("\n\n")) !== -1) {
        const frame = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        const ev = parseFrame(frame);
        if (ev) yield ev;
      }
    }
    buf += decoder.decode();
    if (buf.trim()) {
      const ev = parseFrame(buf);
      if (ev) yield ev;
    }
  } finally {
    reader.releaseLock();
  }
}
