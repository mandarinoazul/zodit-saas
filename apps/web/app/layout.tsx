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
          <header className="border-b border-white/5 p-4 bg-black/40 backdrop-blur-xl sticky top-0 z-50">
            <div className="container mx-auto flex justify-between items-center px-4 md:px-6">
              <div className="flex items-center gap-3 group cursor-pointer">
                <div className="w-8 h-8 bg-gradient-to-br from-gold to-yellow-600 rounded-lg shadow-[0_0_15px_rgba(255,215,0,0.3)] group-hover:shadow-[0_0_25px_rgba(255,215,0,0.5)] transition-all" />
                <h1 className="text-xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">ZODIT GOLD</h1>
              </div>
              <nav className="hidden md:flex gap-8 text-[13px] font-bold uppercase tracking-widest text-white/40">
                <a href="#" className="hover:text-gold text-white transition-colors">Commander</a>
                <a href="#" className="hover:text-gold transition-colors">Neural Assets</a>
                <a href="#" className="hover:text-gold transition-colors">Subscription</a>
                <a href="#" className="hover:text-gold transition-colors">Node Settings</a>
              </nav>
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                <span className="text-[10px] font-bold text-emerald-500 tracking-widest uppercase">System Online</span>
              </div>
            </div>
          </header>
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
          <footer className="p-8 border-t border-white/5 text-center text-white/20 text-xs font-medium tracking-tight">
            &copy; 2026 ZODIT GOLD. SOBERANÍA DE DATOS TOTAL.
          </footer>
        </main>
      </body>
    </html>
  );
}
