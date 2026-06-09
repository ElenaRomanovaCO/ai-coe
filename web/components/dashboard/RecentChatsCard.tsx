import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChatSession } from "@/lib/dashboard";

export function RecentChatsCard({
  chats,
  onResume,
}: {
  chats: ChatSession[];
  onResume: () => void;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Recent Chats</CardTitle>
      </CardHeader>
      <CardContent>
        {chats.length === 0 ? (
          <p className="text-sm text-neutral-400">No conversations yet. Open the chat dock to start.</p>
        ) : (
          <ul className="space-y-2">
            {chats.slice(0, 5).map((c) => (
              <li key={c.session_id} className="flex items-center justify-between gap-2">
                <span className="truncate text-sm text-neutral-700">
                  {c.snippet || "(empty conversation)"}
                </span>
                <Button variant="ghost" size="sm" onClick={onResume} className="shrink-0">
                  Resume
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
