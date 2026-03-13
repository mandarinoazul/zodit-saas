import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zodit Gold | Advanced AI Control",
  description: "Enterprise-grade local AI agent dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-black text-white antialiased font-[family-name:Inter,sans-serif]">
        <div className="fixed inset-0 bg-[url('/hero-bg.png')] bg-cover bg-center opacity-10 pointer-events-none" />
        <div className="fixed inset-0 bg-gradient-to-b from-black via-zinc-950/50 to-black pointer-events-none" />
        
        <main className="relative min-h-screen flex flex-col z-10">
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
