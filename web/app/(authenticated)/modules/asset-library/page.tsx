import { AssetBrowser } from "@/components/AssetBrowser";

import { listAssets } from "./actions";

export const dynamic = "force-dynamic"; // assets come from S3 via the module Lambda

export default async function AssetLibraryPage() {
  const { assets } = await listAssets();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Asset Library</h1>
        <p className="text-sm text-neutral-500">
          {assets.length} curated AI delivery assets — reference architectures, patterns, and
          templates.
        </p>
      </div>
      <AssetBrowser assets={assets} />
    </div>
  );
}
