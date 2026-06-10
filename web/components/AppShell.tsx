"use client";

import { useState } from "react";
import { PanelLeftClose, PanelLeftOpen, X } from "lucide-react";

import { Header } from "@/components/header";
import { Sidebar } from "@/components/Sidebar";
import { cn } from "@/lib/utils";

// The persistent authenticated frame: header (top) + sidebar (left, collapsible)
// + content slot. On narrow screens the sidebar becomes a slide-over drawer
// opened from the header menu button. The chat dock is mounted separately in the
// layout and floats over the bottom-right.
export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen">
      <Header onMenu={() => setMobileOpen(true)} />

      <div className="flex">
        {/* Desktop sidebar */}
        <div className="sticky top-14 hidden h-[calc(100vh-3.5rem)] lg:block">
          <Sidebar collapsed={collapsed} />
          <button
            onClick={() => setCollapsed((c) => !c)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="absolute bottom-3 left-0 flex w-full items-center justify-center py-1 text-slate-400 hover:text-slate-700"
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
        </div>

        {/* Mobile slide-over */}
        {mobileOpen && (
          <div className="fixed inset-0 z-40 lg:hidden">
            <button
              aria-label="Close navigation"
              className="absolute inset-0 bg-slate-900/40"
              onClick={() => setMobileOpen(false)}
            />
            <div className="absolute left-0 top-0 h-full bg-white shadow-xl">
              <div className="flex h-14 items-center justify-between border-b border-slate-200 px-3">
                <span className="font-semibold">Modules</span>
                <button onClick={() => setMobileOpen(false)} aria-label="Close">
                  <X className="h-5 w-5 text-slate-500" />
                </button>
              </div>
              <Sidebar onNavigate={() => setMobileOpen(false)} />
            </div>
          </div>
        )}

        <main className={cn("min-w-0 flex-1 p-6")}>{children}</main>
      </div>
    </div>
  );
}
