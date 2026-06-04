"use client";

import { useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { getDisplayName, logout } from "@/lib/auth";

// Read the client-only display name without a hydration mismatch: the server
// snapshot is null, the client snapshot reads localStorage.
const noopSubscribe = () => () => {};

export function Header() {
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

  return (
    <header className="flex items-center justify-between border-b border-neutral-200 px-6 py-3">
      <span className="font-semibold">AI CoE Platform</span>
      <div className="flex items-center gap-3 text-sm">
        {name && <span className="text-neutral-600">Signed in as {name}</span>}
        <Button variant="outline" size="sm" onClick={onLogout}>
          Log out
        </Button>
      </div>
    </header>
  );
}
