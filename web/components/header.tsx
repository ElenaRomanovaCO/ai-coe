"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getDisplayName, logout } from "@/lib/auth";

// Read the client-only display name without a hydration mismatch.
const noopSubscribe = () => () => {};

export function Header({ onMenu }: { onMenu?: () => void }) {
  const router = useRouter();
  const name = useSyncExternalStore(
    noopSubscribe,
    () => getDisplayName(),
    () => null,
  );

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  const initial = (name ?? "").trim().charAt(0).toUpperCase() || "?";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
      <div className="flex items-center gap-2">
        <button
          onClick={onMenu}
          aria-label="Open navigation"
          className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-indigo-600 text-[10px] font-bold text-white">
            AI
          </span>
          <span className="text-base font-semibold tracking-tight text-slate-900">AI CoE</span>
        </Link>
      </div>

      <div className="flex items-center gap-3 text-sm">
        {name && (
          <span className="hidden items-center gap-2 sm:flex">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
              {initial}
            </span>
            <span className="text-slate-600">{name}</span>
          </span>
        )}
        <Button variant="outline" size="sm" onClick={onLogout}>
          <LogOut className="h-4 w-4" /> Log out
        </Button>
      </div>
    </header>
  );
}
