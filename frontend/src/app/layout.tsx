import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ErrorBoundary } from "@/components/error-boundary";
import { TemaProvider } from "@/components/providers/tema-provider";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Wargio — Asisten Warung",
  description:
    "AI agent untuk pemilik warung Indonesia — stok, hutang, penjualan.",
};

const skripTemaAwal = `
(function () {
  try {
    var t = localStorage.getItem("wargio-tema");
    var gelap =
      t === "dark" ||
      (!t && window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.toggle("dark", gelap);
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" suppressHydrationWarning className={`${inter.variable} h-full`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: skripTemaAwal }} />
      </head>
      <body className="min-h-full antialiased">
        <TemaProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </TemaProvider>
      </body>
    </html>
  );
}
