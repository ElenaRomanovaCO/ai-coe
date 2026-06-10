"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_GROUPS, type NavItem } from "@/lib/nav";
import { cn } from "@/lib/utils";

// Left sidebar nav. Live modules link + highlight on the active route (indigo);
// disabled modules render muted with a "coming soon" tooltip. Collapses to an
// icon-only rail. `onNavigate` lets the mobile drawer close on selection.
export function Sidebar({
  collapsed = false,
  onNavigate,
}: {
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Modules"
      className={cn(
        "flex h-full flex-col gap-5 overflow-y-auto border-r border-slate-200 bg-white py-4",
        collapsed ? "w-16 px-2" : "w-60 px-3",
      )}
    >
      {NAV_GROUPS.map((group) => (
        <div key={group.title}>
          {!collapsed && (
            <h2 className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              {group.title}
            </h2>
          )}
          <ul className="space-y-0.5">
            {group.items.map((item) => (
              <li key={item.id}>
                <NavRow item={item} active={item.route === pathname} collapsed={collapsed} onNavigate={onNavigate} />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function NavRow({
  item,
  active,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  active: boolean;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  const base = cn(
    "group flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm",
    collapsed && "justify-center",
  );

  const inner = (
    <>
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
      {!collapsed && !item.enabled && (
        <span className="rounded bg-slate-100 px-1 text-[10px] text-slate-400">W{item.wave}</span>
      )}
    </>
  );

  if (item.enabled && item.route) {
    return (
      <Link
        href={item.route}
        onClick={onNavigate}
        title={collapsed ? item.label : undefined}
        aria-current={active ? "page" : undefined}
        className={cn(
          base,
          active
            ? "bg-indigo-50 font-medium text-indigo-700"
            : "text-slate-700 hover:bg-slate-100",
        )}
      >
        {inner}
      </Link>
    );
  }

  return (
    <span
      title={`${item.label} — ${item.purpose} (coming soon, wave ${item.wave})`}
      aria-disabled="true"
      className={cn(base, "cursor-not-allowed text-slate-400")}
    >
      {inner}
    </span>
  );
}
