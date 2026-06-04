import { Header } from "@/components/header";

export default function AuthenticatedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="p-6">{children}</main>
    </div>
  );
}
