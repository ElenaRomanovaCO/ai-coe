import { AppShell } from "@/components/AppShell";
import { ChatDock } from "@/components/ChatDock";

export default function AuthenticatedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <AppShell>{children}</AppShell>
      {/* Mounted outside AppShell's flow so the dock persists across navigation
          within an authenticated session and floats over the bottom-right. */}
      <ChatDock />
    </>
  );
}
