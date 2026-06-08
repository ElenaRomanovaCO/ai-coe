import { ChatDock } from "@/components/ChatDock";
import { Header } from "@/components/header";

export default function AuthenticatedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="p-6">{children}</main>
      {/* Mounted in the layout so the dock persists across navigation within an
          authenticated session (the layout doesn't remount between child routes). */}
      <ChatDock />
    </div>
  );
}
