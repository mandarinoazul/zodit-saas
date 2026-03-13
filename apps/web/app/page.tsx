"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, Terminal as TerminalIcon, ShieldCheck, Zap } from "lucide-react";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [isLogged, setIsLogged] = useState(false);
  const [activeTab, setActiveTab] = useState<'commander' | 'assets' | 'billing' | 'nodes'>('commander');
  const [command, setCommand] = useState("");
  const [responses, setResponses] = useState<{ type: 'user' | 'bot' | 'error', text: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const tab = searchParams.get('tab') as any;
    if (tab && ['commander', 'assets', 'billing', 'nodes'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);

  if (!isLogged) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-zinc-900/60 border border-white/5 rounded-[40px] p-12 space-y-8 backdrop-blur-3xl shadow-2xl animate-in fade-in zoom-in duration-700">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-black tracking-tighter uppercase">Neural Access</h2>
            <p className="text-gold text-[10px] font-black uppercase tracking-[0.2em]">Authentication Required</p>
          </div>
          <div className="space-y-4">
            <input type="password" placeholder="Access Key" className="w-full bg-black/60 border border-white/5 rounded-2xl px-6 py-4 font-bold placeholder:text-white/10 text-center" />
            <button 
              onClick={() => setIsLogged(true)}
              className="w-full bg-white text-black font-black uppercase tracking-widest text-xs py-5 rounded-2xl hover:bg-gold transition-all shadow-xl"
            >
              Verify Identity
            </button>
            <p className="text-center text-[9px] text-white/20 font-bold uppercase tracking-widest pt-4">Sovereign Data Protection Active</p>
          </div>
        </div>
      </div>
    );
  }

  const handleExecute = async () => {
    if (!command.trim()) return;

    const userMessage = command;
    setCommand("");
    setResponses((prev: any) => [...prev, { type: 'user', text: userMessage }]);
    setIsLoading(true);

    try {
      const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "";
      const gatewayKey = process.env.NEXT_PUBLIC_GATEWAY_SECRET || ""; // Should be ZODIT_API_KEY
      
      if (!gatewayUrl) throw new Error("Gateway URL not configured.");

      const res = await fetch(`${gatewayUrl}/agent/execute`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-API-Key": gatewayKey 
        },
        body: JSON.stringify({ command: userMessage }),
      });

      if (!res.ok) {
        if (res.status === 401) throw new Error("Authentication failed. Check GATEWAY_SECRET.");
        if (res.status === 403) throw new Error("Subscription required or invalid tier.");
        if (res.status === 502) throw new Error("Cloud Gateway cannot reach your Local Agent.");
        throw new Error(`Status: ${res.status}`);
      }

      const data = await res.json();
      setResponses((prev: any) => [...prev, { type: 'bot', text: data.response || JSON.stringify(data) }]);
    } catch (error: any) {
      setResponses((prev: any) => [...prev, { type: 'error', text: `Connection Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const setTab = (tab: string) => {
    router.push(`?tab=${tab}`);
    setActiveTab(tab as any);
  };

  return (
    <div className="flex-1 container mx-auto px-4 md:px-8 py-8 md:py-12">
      <div className="max-w-5xl mx-auto space-y-12">
        
        {/* Superior Navigation Tabs */}
        <div className="flex justify-center md:justify-start border-b border-white/5 pb-1 gap-8 overflow-x-auto no-scrollbar">
          {(['commander', 'assets', 'billing', 'nodes'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setTab(tab)}
              className={`pb-4 text-[11px] uppercase tracking-[0.2em] font-black transition-all relative ${
                activeTab === tab ? 'text-gold' : 'text-white/30 hover:text-white/60'
              }`}
            >
              {tab}
              {activeTab === tab && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gold rounded-full shadow-[0_-5px_15px_rgba(255,215,0,0.5)]" />
              )}
            </button>
          ))}
        </div>

        {activeTab === 'commander' && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Hero Section */}
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gold/10 border border-gold/20 text-[10px] uppercase tracking-widest font-bold text-gold">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-gold"></span>
                </span>
                Neural Connection: Stable
              </div>
              <h2 className="text-4xl md:text-6xl font-black tracking-tighter leading-[0.9]">
                Ready for <span className="bg-clip-text text-transparent bg-gradient-to-r from-gold via-yellow-400 to-gold/50 text-glow">Input.</span>
              </h2>
            </div>

            {/* Neural Terminal */}
            {responses.length > 0 && (
              <div className="bg-black/90 border border-white/5 rounded-3xl p-6 font-mono text-[13px] space-y-4 max-h-[350px] overflow-y-auto scrollbar-hide shadow-2xl backdrop-blur-3xl">
                <div className="flex items-center gap-2 text-white/20 border-b border-white/5 pb-3 mb-4">
                  <TerminalIcon size={12} />
                  <span className="uppercase tracking-widest text-[9px] font-black">Secure Data Stream</span>
                </div>
                {responses.map((r, i) => (
                  <div key={i} className={`flex gap-3 ${r.type === 'user' ? 'text-white/30' : r.type === 'error' ? 'text-red-500' : 'text-white/90'}`}>
                    <span className="shrink-0 opacity-50 font-black">{r.type === 'user' ? 'USR>' : r.type === 'error' ? 'ERR!' : 'SYS#'}</span>
                    <p className="leading-relaxed whitespace-pre-wrap">{r.text}</p>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex items-center gap-3 text-gold animate-pulse">
                    <Loader2 className="animate-spin" size={12} />
                    <span className="text-[10px] uppercase tracking-widest font-black">Syncing Neural Pathway...</span>
                  </div>
                )}
              </div>
            )}

            {/* Command Interface */}
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-gold/10 to-transparent rounded-[32px] blur-2xl opacity-50 group-hover:opacity-100 transition duration-700" />
              <div className="relative bg-zinc-900/60 border border-white/5 backdrop-blur-2xl rounded-[32px] p-8 md:p-10 space-y-8 shadow-inner">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full border border-gold/30 flex items-center justify-center text-gold shadow-[0_0_15px_rgba(255,215,0,0.1)]">
                      <ShieldCheck size={20} />
                    </div>
                    <div>
                      <h3 className="text-xl font-black tracking-tight uppercase">Strategic Nexus</h3>
                      <p className="text-[10px] text-white/30 font-bold tracking-[0.2em] uppercase">Private Encryption Active</p>
                    </div>
                  </div>
                </div>
                <div className="relative flex flex-col md:flex-row gap-4">
                  <input 
                    type="text" 
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
                    placeholder="Enter strategic instruction..." 
                    className="flex-1 bg-black/60 border border-white/5 rounded-2xl px-6 py-5 text-lg focus:outline-none focus:border-gold/30 transition-all font-bold placeholder:text-white/10 text-white shadow-2xl"
                    disabled={isLoading}
                  />
                  <button 
                    onClick={handleExecute}
                    disabled={isLoading}
                    className="bg-gradient-to-br from-gold to-yellow-600 text-black font-black uppercase tracking-[0.2em] text-[12px] px-12 py-5 rounded-2xl shadow-[0_15px_30px_rgba(255,215,0,0.2)] hover:shadow-[0_20px_40px_rgba(255,215,0,0.3)] hover:-translate-y-1 active:translate-y-0 transition-all disabled:opacity-30 flex items-center justify-center gap-3"
                  >
                    {isLoading ? <Loader2 className="animate-spin" /> : <Zap size={16} fill="currentColor" />}
                    {isLoading ? "Sync" : "Execute"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'assets' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <SkillCard title="PC Automation" desc="Control Windows filesystem and apps." icon="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" status="ready" />
            <SkillCard title="WhatsApp Engine" desc="Read and send encrypted messages." icon="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-7.6 8.38 8.38 0 0 1 3.8.9L21 3.5z" status="ready" />
            <SkillCard title="Sovereign Memory" desc="RAG storage for private records." icon="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" status="ready" />
            <SkillCard title="Voice Synthesis" desc="Text-to-speech local pipeline." icon="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z M3 10v1a9 9 0 0 0 18 0v-1" status="locked" />
            <SkillCard title="Video Analysis" desc="Analyze local CCTV or webcam leaks." icon="M23 7l-7 5 7 5V7z M1 5h14v14H1V5z" status="locked" />
          </div>
        )}

        {activeTab === 'billing' && (
          <div className="bg-zinc-900/60 border border-white/5 rounded-[40px] p-10 md:p-16 text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="w-20 h-20 bg-gold/10 rounded-full flex items-center justify-center mx-auto text-gold mb-4 border border-gold/20">
              <Zap size={40} fill="currentColor" />
            </div>
            <div className="space-y-2">
              <h3 className="text-4xl font-black tracking-tighter">Sovereign Tier: PRO</h3>
              <p className="text-white/40 tracking-widest text-xs font-black uppercase">Managed via Polar.sh</p>
            </div>
            <div className="max-w-md mx-auto p-4 border border-white/5 rounded-2xl bg-black/40 text-sm font-bold text-white/60">
              Subscription Renews: April 12, 2026
            </div>
            <button className="px-10 py-4 bg-white/5 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-all">
              Manage Billing Details
            </button>
          </div>
        )}

        {activeTab === 'nodes' && (
          <div className="bg-zinc-900/60 border border-white/5 rounded-[40px] p-10 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between border-b border-white/5 pb-8">
              <div className="space-y-1">
                <h3 className="text-xl font-black uppercase tracking-tight">Main Local Node</h3>
                <p className="text-xs font-bold text-emerald-500 tracking-widest uppercase">mandev.site (Online)</p>
              </div>
              <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-xl text-[10px] font-black uppercase tracking-widest">
                Linked
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 bg-black/40 rounded-3xl border border-white/5 space-y-4">
                <h4 className="text-[10px] font-black uppercase tracking-widest text-white/30">Node Agent ID</h4>
                <p className="font-mono text-sm text-gold truncate">zodit-node-f8ad510-mandev</p>
              </div>
              <div className="p-6 bg-black/40 rounded-3xl border border-white/5 space-y-4">
                <h4 className="text-[10px] font-black uppercase tracking-widest text-white/30">Gateway Endpoint</h4>
                <p className="font-mono text-sm text-white/60 truncate">zodit-gateway.railway.app</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen text-gold font-black uppercase tracking-widest">Neural Sync...</div>}>
      <DashboardContent />
    </Suspense>
  );
}

function SkillCard({ title, desc, icon, status }: { title: string; desc: string; icon: string; status?: 'ready' | 'locked' }) {
  return (
    <div className={`group relative bg-zinc-900/30 border p-8 rounded-[32px] transition-all overflow-hidden ${
      status === 'locked' ? 'border-white/5 opacity-50 grayscale' : 'border-white/5 hover:border-gold/30 cursor-pointer shadow-2xl'
    }`}>
      <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-20 group-hover:scale-110 transition-all duration-700">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gold">
          <path d={icon} />
        </svg>
      </div>
      <div className="space-y-4 relative z-10">
        <div className={`w-12 h-1 rounded-full transition-all duration-700 ${
          status === 'locked' ? 'bg-white/10' : 'bg-gold/20 group-hover:w-20 group-hover:bg-gold'
        }`} />
        <div>
          <h3 className="text-xl font-black tracking-tight uppercase">{title}</h3>
          {status === 'locked' && <p className="text-[9px] font-black text-gold uppercase tracking-[0.2em] mt-1">Expansion Pack Needed</p>}
        </div>
        <p className="text-xs text-white/40 font-bold leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

