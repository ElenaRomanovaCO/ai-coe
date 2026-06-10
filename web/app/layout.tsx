import type { Metadata } from "next";
import { Hanken_Grotesk } from "next/font/google";
import "./globals.css";

// Praxis design system typeface (design-system.md / the design mocks use Hanken Grotesk).
const hanken = Hanken_Grotesk({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Praxis — AI CoE Platform",
  description: "Internal AI Center of Excellence platform",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={hanken.className}>
      <body>{children}</body>
    </html>
  );
}
