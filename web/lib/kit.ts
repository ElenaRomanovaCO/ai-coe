// Kit Builder types, mirroring AGENT-04 (agents/lambdas/modules/agent_04_kit_builder.py).

export const KIT_AGENT_ID = "AGENT-04";

export const ENGAGEMENT_TYPES = ["discovery", "pilot", "scale", "optimize"] as const;
export const KIT_CATEGORIES = [
  "architecture",
  "templates",
  "governance",
  "intelligence",
  "tools",
] as const;

export interface KitFile {
  category: string;
  source_path: string;
  target_path: string;
  title: string;
  rationale: string;
}

export interface KitManifest {
  status: string;
  kit_id: string;
  kit_slug: string;
  files: KitFile[];
  readme_markdown: string;
  download_url: string | null;
  zip_key?: string;
}

export interface VaultFile {
  source_path: string;
  title: string;
  content_type: string;
}

// content_type prefix (from search_vault) -> kit category.
export function categoryForContentType(ct: string): string {
  return (
    { assets: "architecture", regs: "governance", feed: "intelligence", tools: "tools" }[ct] ??
    "architecture"
  );
}
