"use server";

// Server actions for the Intelligence Feed. Invoke AGENT-23 in the module-agents
// Lambda (which fans out to WORKER-10/11 via the workers Lambda). Under
// (authenticated), so the middleware gates callers. Like the compliance actions, this
// is a plain invoke (AGENT-23 is non-streaming).

import { invokeModule } from "@/lib/aws";
import {
  FEED_AGENT_ID,
  type FeedProfile,
  type GetFeedItemResult,
  type ListFeedResult,
  type RadarViewResult,
} from "@/lib/feed";

export async function listFeed(
  filters: {
    category?: string;
    industry?: string;
    radar_status?: string;
    user_profile?: FeedProfile;
  } = {},
): Promise<ListFeedResult> {
  return invokeModule<ListFeedResult>(FEED_AGENT_ID, { op: "list", ...filters });
}

export async function getFeedItem(
  itemId: string,
  profile: FeedProfile = { industries: [] },
): Promise<GetFeedItemResult> {
  return invokeModule<GetFeedItemResult>(FEED_AGENT_ID, {
    op: "get",
    item_id: itemId,
    user_profile: profile,
  });
}

export async function getRadar(): Promise<RadarViewResult> {
  return invokeModule<RadarViewResult>(FEED_AGENT_ID, { op: "radar" });
}
