// Renders an asset's frontmatter as labeled rows. Arrays render as chips; scalars
// as text. Long/nested values are JSON-stringified as a fallback.

function renderValue(value: unknown) {
  if (Array.isArray(value)) {
    return (
      <div className="flex flex-wrap gap-1">
        {value.map((v, i) => (
          <span
            key={i}
            className="rounded bg-neutral-100 px-1.5 py-0.5 text-xs text-neutral-700"
          >
            {String(v)}
          </span>
        ))}
      </div>
    );
  }
  if (value === null || value === undefined) return <span className="text-neutral-400">—</span>;
  if (typeof value === "object") {
    return <code className="text-xs">{JSON.stringify(value)}</code>;
  }
  return <span>{String(value)}</span>;
}

function label(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function FrontmatterPanel({ frontmatter }: { frontmatter: Record<string, unknown> }) {
  const entries = Object.entries(frontmatter ?? {});
  return (
    <dl className="space-y-3 text-sm">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt className="text-xs font-medium uppercase tracking-wide text-neutral-500">
            {label(key)}
          </dt>
          <dd className="mt-1 text-neutral-800">{renderValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
}
