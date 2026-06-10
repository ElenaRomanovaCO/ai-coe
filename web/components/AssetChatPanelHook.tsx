"use client";

import { useState } from "react";
import { MessageSquareText } from "lucide-react";

import { AssetChatPanel } from "@/components/AssetChatPanel";
import { Button } from "@/components/ui/button";

export interface AssetChatPanelHookProps {
  assetId: string;
  assetTitle: string;
  assetContent: string;
  assetFrontmatter: Record<string, unknown>;
}

// Drop-in for any asset detail page: a "Chat with this" button wired to the scoped
// Q&A side panel. Later detail pages (Compliance, Vendor Eval, Intelligence Feed)
// embed the same pattern — pass the page's asset id/title/body/frontmatter.
export function AssetChatPanelHook({
  assetId,
  assetTitle,
  assetContent,
  assetFrontmatter,
}: AssetChatPanelHookProps) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button size="sm" className="w-full" onClick={() => setOpen(true)}>
        <MessageSquareText className="h-4 w-4" />
        Chat with this
      </Button>
      <AssetChatPanel
        open={open}
        onClose={() => setOpen(false)}
        assetId={assetId}
        assetTitle={assetTitle}
        assetContent={assetContent}
        assetFrontmatter={assetFrontmatter}
      />
    </>
  );
}
