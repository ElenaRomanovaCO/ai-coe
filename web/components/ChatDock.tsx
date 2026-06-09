"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { MessageCircle, Send, Square, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { OPEN_CHAT_EVENT } from "@/lib/dashboard";
import { parseSSE } from "@/lib/sse";
import { cn } from "@/lib/utils";

interface Citation {
  file_path: string;
  chunk_index: number;
  content_type: string;
  asset_library_url?: string | null;
  score?: number | null;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  pending?: boolean;
  error?: boolean;
}

// Per-tab persistence: sessionStorage survives refresh (restores history) but is
// not shared across tabs (a new tab starts a new session) — exactly the spec's
// session semantics, with no S3 read needed on the client.
const SESSION_KEY = "aicoe_chat_session";
const MESSAGES_KEY = "aicoe_chat_messages";

function newSessionId(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `s_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

export function ChatDock() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  // Lazy-hydrate the transcript from sessionStorage (guarded for SSR). The dock
  // renders closed at first paint, so this never causes a hydration mismatch.
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = window.sessionStorage.getItem(MESSAGES_KEY);
      return stored ? (JSON.parse(stored) as Message[]) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const sessionIdRef = useRef<string>("");
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Establish the per-tab session id on mount (ref only — no setState here).
  useEffect(() => {
    let sid = window.sessionStorage.getItem(SESSION_KEY);
    if (!sid) {
      sid = newSessionId();
      window.sessionStorage.setItem(SESSION_KEY, sid);
    }
    sessionIdRef.current = sid;
  }, []);

  // Persist transcript so a refresh restores history within the same tab.
  useEffect(() => {
    if (messages.length) {
      window.sessionStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
    }
  }, [messages]);

  // The dashboard's "Resume Last Chat" / "Resume" buttons open the dock via this
  // window event (cross-component, since the dock lives in the layout).
  useEffect(() => {
    const open = () => setOpen(true);
    window.addEventListener(OPEN_CHAT_EVENT, open);
    return () => window.removeEventListener(OPEN_CHAT_EVENT, open);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, open]);

  const updateLastAssistant = useCallback((fn: (m: Message) => Message) => {
    setMessages((prev) => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i--) {
        if (next[i].role === "assistant") {
          next[i] = fn(next[i]);
          break;
        }
      }
      return next;
    });
  }, []);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", text },
      { role: "assistant", text: "", pending: true },
    ]);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionIdRef.current,
          display_name: getDisplayName() ?? "Guest",
          current_route: pathname,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        updateLastAssistant((m) => ({
          ...m,
          pending: false,
          error: true,
          text: "Sorry — I couldn't reach the assistant. Please try again.",
        }));
        return;
      }

      for await (const ev of parseSSE(res.body)) {
        if (ev.event === "token") {
          const t = (ev.data as { text?: string }).text ?? "";
          updateLastAssistant((m) => ({ ...m, pending: false, text: m.text + t }));
        } else if (ev.event === "citation") {
          const c = ev.data as Citation;
          updateLastAssistant((m) => ({ ...m, citations: [...(m.citations ?? []), c] }));
        } else if (ev.event === "done") {
          const d = ev.data as { assistant_message?: string; citations?: Citation[] };
          updateLastAssistant((m) => ({
            ...m,
            pending: false,
            text: m.text || d.assistant_message || "",
            citations: d.citations?.length ? d.citations : m.citations,
          }));
        } else if (ev.event === "error") {
          updateLastAssistant((m) => ({
            ...m,
            pending: false,
            error: true,
            text: (ev.data as { message?: string }).message ?? "Something went wrong.",
          }));
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        updateLastAssistant((m) => ({
          ...m,
          pending: false,
          error: true,
          text: m.text || "The connection was interrupted.",
        }));
      } else {
        updateLastAssistant((m) => ({ ...m, pending: false }));
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, streaming, pathname, updateLastAssistant]);

  function stop() {
    abortRef.current?.abort();
  }

  if (!open) {
    return (
      <button
        aria-label="Open chat"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-900 text-white shadow-lg transition-colors hover:bg-neutral-800"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex h-[32rem] w-[24rem] max-w-[calc(100vw-2.5rem)] flex-col rounded-xl border border-neutral-200 bg-white shadow-2xl">
      <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3">
        <span className="text-sm font-semibold">AI CoE Assistant</span>
        <button aria-label="Close chat" onClick={() => setOpen(false)}>
          <X className="h-4 w-4 text-neutral-500 hover:text-neutral-900" />
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {messages.length === 0 && (
          <p className="mt-8 text-center text-sm text-neutral-400">
            Ask about the vault, the platform&apos;s modules, or what to do next.
          </p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
      </div>

      <form
        className="flex items-center gap-2 border-t border-neutral-200 p-3"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={streaming}
          autoFocus
        />
        {streaming ? (
          <Button type="button" variant="outline" size="sm" onClick={stop} aria-label="Stop">
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button type="submit" size="sm" disabled={!input.trim()} aria-label="Send">
            <Send className="h-4 w-4" />
          </Button>
        )}
      </form>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-lg px-3 py-2 text-sm",
          isUser
            ? "bg-neutral-900 text-white"
            : message.error
              ? "bg-red-50 text-red-700"
              : "bg-neutral-100 text-neutral-900",
        )}
      >
        {message.pending && !message.text ? (
          <span className="inline-flex gap-1">
            <Dot /> <Dot /> <Dot />
          </span>
        ) : (
          <span className="whitespace-pre-wrap">{message.text}</span>
        )}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.citations.map((c, i) => (
              <CitationBadge key={`${c.file_path}#${c.chunk_index}-${i}`} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CitationBadge({ citation }: { citation: Citation }) {
  const label = citation.file_path.split("/").pop() ?? citation.file_path;
  const className =
    "inline-block rounded border border-neutral-300 bg-white px-1.5 py-0.5 text-[11px] text-neutral-700 hover:bg-neutral-50";
  if (citation.asset_library_url) {
    return (
      <a href={citation.asset_library_url} title={citation.file_path} className={className}>
        {label}
      </a>
    );
  }
  return (
    <span title={citation.file_path} className={className}>
      {label}
    </span>
  );
}

function Dot() {
  return <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-neutral-400" />;
}
