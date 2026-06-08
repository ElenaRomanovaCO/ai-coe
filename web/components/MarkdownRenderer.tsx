import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

// Renders sanitized markdown with explicit element styling (no typography plugin
// dependency). GFM gives tables/strikethrough/task lists; rehype-sanitize strips
// any unsafe HTML in the source.
const components: Components = {
  h1: (props) => <h1 className="mt-6 mb-3 text-2xl font-semibold" {...props} />,
  h2: (props) => <h2 className="mt-6 mb-2 text-xl font-semibold" {...props} />,
  h3: (props) => <h3 className="mt-4 mb-2 text-lg font-semibold" {...props} />,
  p: (props) => <p className="my-3 leading-7 text-neutral-800" {...props} />,
  ul: (props) => <ul className="my-3 list-disc space-y-1 pl-6" {...props} />,
  ol: (props) => <ol className="my-3 list-decimal space-y-1 pl-6" {...props} />,
  li: (props) => <li className="leading-7" {...props} />,
  a: (props) => <a className="text-blue-600 underline hover:text-blue-800" {...props} />,
  blockquote: (props) => (
    <blockquote className="my-3 border-l-4 border-neutral-300 pl-4 text-neutral-600" {...props} />
  ),
  code: (props) => (
    <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-sm" {...props} />
  ),
  pre: (props) => (
    <pre className="my-3 overflow-x-auto rounded-lg bg-neutral-900 p-4 text-sm text-neutral-100" {...props} />
  ),
  table: (props) => (
    <div className="my-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm" {...props} />
    </div>
  ),
  th: (props) => (
    <th className="border border-neutral-300 bg-neutral-50 px-3 py-2 text-left font-semibold" {...props} />
  ),
  td: (props) => <td className="border border-neutral-300 px-3 py-2 align-top" {...props} />,
  hr: () => <hr className="my-6 border-neutral-200" />,
};

export function MarkdownRenderer({ children }: { children: string }) {
  return (
    <div className="text-[15px]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={components}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
