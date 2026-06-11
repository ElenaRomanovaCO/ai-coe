import { Rss } from "lucide-react";

import { FeedBrowser } from "@/components/feed/FeedBrowser";

import { listFeed } from "./actions";

export const dynamic = "force-dynamic"; // feed items come from S3 via the module Lambda

export default async function IntelligenceFeedPage() {
  // Initial render uses a neutral default profile; the browser's selectors re-rank.
  const { items } = await listFeed({
    user_profile: { industries: ["cross-industry"], ai_stage: 2 },
  });

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Rss className="h-6 w-6 text-indigo-600" />
          AI Intelligence Feed
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {items.length} curated AI developments, ranked for your focus. Open one for a tailored
          &ldquo;what this means for you&rdquo; note, or jump to the release radar.
        </p>
      </div>
      <FeedBrowser initialItems={items} />
    </div>
  );
}
