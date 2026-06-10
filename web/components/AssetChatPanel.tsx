"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send, X } from "lucide-react";

import { askAsset } from "@/app/actions/asset_qa";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { type AssetQACitation } from "@/lib/assetQa";
import { cn } from "@/lib/utils";

const DEFAULT_SUGGESTIONS = [
  "Summarize this for an executive",
  "What are the key risks or considerations?",
  "Turn this into an action checklist",
  "Compare this to similar assets",
];

interface PanelMessage {
  role: "user" | "assistant";
  text: string;
  citations?: AssetQACitation[];
  pending?: boolean;
  error?: boolean;
}

export interface AssetChatPanelProps {
  open: boolean;
  onClose: () => void;
  assetId: string;
  assetTitle: string;
  assetContent: string;
  assetFrontmatter: Record<string, unknown>;
}

function newSessionId(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `aq_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

// Side panel that scopes a chat to ONE asset. The asset body + frontmatter are
// sent with every turn (AGENT-25 bakes them into its system prompt). Non-streaming:
// each turn is a single server-action round-trip through the module-agents Lambda.
export function AssetChatPanel({
  open,
  onClose,
  assetId,
  assetTitle,
  assetContent,
  assetFrontmatter,
}: AssetChatPanelProps) {
  const [messages, setMessages] = useState<PanelMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(DEFAULT_SUGGESTIONS);
  const sessionIdRef = useRef<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // One session per asset panel, established lazily on first render.
  if (sessionIdRef.current == null) sessionIdRef.current = newSessionId();

  useEffect(() => {
    if (open) scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, open]);

  // Close on Escape while the panel is open.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const updateLastAssistant = useCallback((fn: (m: PanelMessage) => PanelMessage) => {
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

  const send = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text || loading) return;
      setInput("");
      // Snapshot prior turns as the history the agent replays (exclude the new
      // user turn and any pending/errored assistant bubbles).
      const history = messages
        .filter((m) => m.text && !m.error)
        .map((m) => ({ role: m.role, text: m.text }));
      setMessages((prev) => [
        ...prev,
        { role: "user", text },
        { role: "assistant", text: "", pending: true },
      ]);
      setLoading(true);

      try {
        const res = await askAsset({
          asset_id: assetId,
          asset_content: assetContent,
          asset_frontmatter: assetFrontmatter,
          session_id: sessionIdRef.current ?? newSessionId(),
          message: text,
          history,
          display_name: getDisplayName() ?? "Guest",
        });
        if (res.status === "ok") {
          updateLastAssistant((m) => ({
            ...m,
            pending: false,
            text: res.assistant_message,
            citations: res.citations,
          }));
          if (res.suggestions?.length) setSuggestions(res.suggestions);
        } else {
          updateLastAssistant((m) => ({
            ...m,
            pending: false,
            error: true,
            text: res.message || "Sorry — I couldn't answer that. Please try again.",
          }));
        }
      } catch {
        updateLastAssistant((m) => ({
          ...m,
          pending: false,
          error: true,
          text: "Sorry — I couldn't reach the assistant. Please try again.",
        }));
      } finally {
        setLoading(false);
      }
    },
    [loading, messages, assetId, assetContent, assetFrontmatter, updateLastAssistant],
  );

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        aria-hidden="true"
        onClick={onClose}
      />
      {/* Panel */}
      <aside
        role="dialog"
        aria-label={`Chat with ${assetTitle}`}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-neutral-200 bg-white shadow-2xl"
      >
        <header className="flex items-start justify-between gap-2 border-b border-neutral-200 px-4 py-3">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-indigo-600">
              Chat with this asset
            </p>
            <p className="truncate text-sm font-semibold text-neutral-900">{assetTitle}</p>
          </div>
          <button aria-label="Close chat" onClick={onClose} className="mt-0.5 shrink-0">
            <X className="h-4 w-4 text-neutral-500 hover:text-neutral-900" />
          </button>
        </header>

        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
          {messages.length === 0 && (
            <p className="mt-6 text-center text-sm text-neutral-400">
              Ask anything about <span className="font-medium">{assetTitle}</span> — summaries,
              risks, checklists, or how it compares to other assets.
            </p>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
        </div>

        {/* Quick-prompt suggestions */}
        {!loading && suggestions.length > 0 && (
          <div className="flex flex-wrap gap-1.5 border-t border-neutral-200 px-4 pt-3">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => void send(s)}
                className="rounded-full border border-neutral-300 bg-white px-2.5 py-1 text-xs text-neutral-700 hover:border-indigo-400 hover:text-indigo-700"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          className="flex items-center gap-2 border-t border-neutral-200 p-3"
          onSubmit={(e) => {
            e.preventDefault();
            void send(input);
          }}
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this asset…"
            disabled={loading}
            autoFocus
          />
          <Button type="submit" size="sm" disabled={loading || !input.trim()} aria-label="Send">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </aside>
    </>
  );
}

function MessageBubble({ message }: { message: PanelMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-lg px-3 py-2 text-sm",
          isUser
            ? "bg-indigo-600 text-white"
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
              <CitationBadge key={`${c.asset_id}-${i}`} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CitationBadge({ citation }: { citation: AssetQACitation }) {
  const label = citation.title || citation.asset_id;
  const className =
    "inline-block rounded border border-neutral-300 bg-white px-1.5 py-0.5 text-[11px] text-neutral-700 hover:bg-neutral-50";
  if (citation.asset_library_url) {
    return (
      <a href={citation.asset_library_url} title={citation.asset_id} className={className}>
        {label}
      </a>
    );
  }
  return (
    <span title={citation.asset_id} className={className}>
      {label}
    </span>
  );
}

function Dot() {
  return <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-neutral-400" />;
}
