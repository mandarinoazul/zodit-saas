"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, Terminal as TerminalIcon, ShieldCheck, Zap, Brain, Cpu, CreditCard } from "lucide-react";

import { fetchWithKey } from "../lib/api";
import { supabase } from "../lib/supabase";
import { User } from "@supabase/supabase-js";

function DashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [authEmail, setAuthEmail] = useState("");
  const [authPass, setAuthPass] = useState("");
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [activeTab, setActiveTab] = useState<'commander' | 'knowledge' | 'skills' | 'nodes' | 'billing'>('commander');
  const [command, setCommand] = useState("");
  const [responses, setResponses] = useState<{ type: 'user' | 'bot' | 'error', text: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [skills, setSkills] = useState<{ id: string, enabled: boolean }[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [activeModel, setActiveModel] = useState("");
  const [customNodeUrl, setCustomNodeUrl] = useState('');

  // Authentication & Initial Load
  useEffect(() => {
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user || null);
    };

    checkUser();
    
    // Load custom node from local storage
    if (typeof window !== 'undefined') {
        setCustomNodeUrl(localStorage.getItem('zodit_custom_gateway') || '');
    }

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    const tab = searchParams.get('tab') as any;
    if (tab && ['commander', 'knowledge', 'skills', 'nodes', 'billing'].includes(tab)) {
      setActiveTab(tab);
    }
    // Fetch initial data
    if (user) {
        loadSkills();
        loadModels();
    }
  }, [searchParams, user]);

  const loadSkills = async () => {
      try {
          const data = await fetchWithKey('/api/skills');
          setSkills(data);
      } catch (e) { console.error("Failed to load skills", e); }
  };

  const loadModels = async () => {
    try {
        const data = await fetchWithKey('/api/ollama/models');
        setModels(data);
    } catch (e) { console.error("Failed to load models", e); }
  };

  const toggleSkill = async (id: string, current: boolean) => {
      try {
          await fetchWithKey('/api/skills/toggle', {
              method: 'POST',
              body: JSON.stringify({ id, enabled: !current })
          });
          loadSkills();
      } catch (e) { alert("Error toggling skill"); }
  };

  const switchModel = async (modelName: string) => {
    try {
        await fetchWithKey('/api/system/config', {
            method: 'POST',
            body: JSON.stringify({ model: modelName })
        });
        setActiveModel(modelName);
    } catch (e) { alert("Error switching model"); }
  };

  const handleAuth = async () => {
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
        alert("CRITICAL ERROR: Supabase Environment Variables are missing in Vercel settings.");
        return;
    }
    setIsLoading(true);
    try {
        if (authMode === 'login') {
            const { error } = await supabase.auth.signInWithPassword({ email: authEmail, password: authPass });
            if (error) throw error;
        } else {
            const { error } = await supabase.auth.signUp({ email: authEmail, password: authPass });
            if (error) throw error;
            alert("Check your email for confirmation!");
        }
    } catch (e: any) {
        alert(`Authentication Error: ${e.message || "Failed to reach Supabase"}`);
    } finally {
        setIsLoading(false);
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  if (!user) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 min-h-screen bg-black">
        <div className="max-w-md w-full bg-zinc-900/40 border border-white/5 rounded-[48px] p-12 space-y-10 backdrop-blur-3xl shadow-2xl animate-in fade-in zoom-in duration-1000">
          <div className="text-center space-y-3">
            <div className="w-16 h-16 bg-gold/5 rounded-full flex items-center justify-center mx-auto border border-gold/10 mb-2">
                <ShieldCheck className="text-gold" size={32} />
            </div>
            <h2 className="text-4xl font-black tracking-tighter uppercase italic">Neural <span className="text-gold">SaaS</span></h2>
            <p className="text-gold/60 text-[10px] font-black uppercase tracking-[0.3em]">Accessing Sovereign Node</p>
          </div>
          
          <div className="space-y-6">
            <div className="flex rounded-2xl bg-white/5 p-1 border border-white/5">
                <button 
                  onClick={() => setAuthMode('login')}
                  className={`flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${authMode === 'login' ? 'bg-white text-black' : 'text-white/40'}`}
                >
                    Login
                </button>
                <button 
                  onClick={() => setAuthMode('signup')}
                  className={`flex-1 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${authMode === 'signup' ? 'bg-white text-black' : 'text-white/40'}`}
                >
                    Register
                </button>
            </div>

            <div className="space-y-4">
                <input 
                    type="email" 
                    placeholder="Email Address" 
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    className="w-full bg-black/40 border border-white/5 rounded-2xl px-8 py-5 font-bold placeholder:text-white/5 focus:border-gold/30 transition-all outline-none" 
                />
                <input 
                    type="password" 
                    placeholder="Secure Password" 
                    value={authPass}
                    onChange={(e) => setAuthPass(e.target.value)}
                    className="w-full bg-black/40 border border-white/5 rounded-2xl px-8 py-5 font-bold placeholder:text-white/5 focus:border-gold/30 transition-all outline-none" 
                />
            </div>

            <button 
              onClick={handleAuth}
              disabled={isLoading}
              className="group relative w-full overflow-hidden rounded-3xl"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-gold via-yellow-400 to-gold animate-gradient-x" />
              <div className="relative bg-white/90 hover:bg-transparent text-black font-black uppercase tracking-widest text-[11px] py-6 transition-all flex items-center justify-center gap-3">
                {isLoading ? <Loader2 className="animate-spin" size={16} /> : "Authenticate Identity"}
              </div>
            </button>
          </div>

          <div className="pt-4 flex flex-col items-center gap-1 opacity-20 hover:opacity-100 transition-opacity">
            <p className="text-[8px] font-black uppercase tracking-[0.4em]">Zodit Gold Security Engine</p>
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
      const data = await fetchWithKey('/api/chat', {
        method: "POST",
        body: JSON.stringify({ message: userMessage }),
      });
      setResponses((prev: any) => [...prev, { type: 'bot', text: data.response || JSON.stringify(data) }]);
    } catch (error: any) {
      setResponses((prev: any) => [...prev, { type: 'error', text: `Connection Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-black text-white font-sans selection:bg-gold/30">
      
      {/* PROFESSIONAL SIDEBAR */}
      <aside className="w-24 md:w-80 border-r border-white/5 flex flex-col bg-zinc-950/50 backdrop-blur-3xl shrink-0 transition-all">
        <div className="p-8 pb-12">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gold flex items-center justify-center shadow-[0_0_20px_rgba(255,215,0,0.3)]">
                    <Zap className="text-black" size={20} fill="currentColor" />
                </div>
                <div className="hidden md:block">
                    <h1 className="text-xl font-black tracking-tighter uppercase italic">Zodit <span className="text-gold">Gold</span></h1>
                    <p className="text-[8px] font-black tracking-[0.3em] uppercase opacity-40">Elite OS v5.0</p>
                </div>
            </div>
        </div>

        {/* Dashboard Navigation */}
            <div className="flex-1 px-4 space-y-2 py-6">
              <SideItem id="commander" icon={<TerminalIcon size={18}/>} label="Commander" active={activeTab === 'commander'} onClick={() => setActiveTab('commander')} />
              <SideItem id="knowledge" icon={<Brain size={18}/>} label="Knowledge" active={activeTab === 'knowledge'} onClick={() => setActiveTab('knowledge')} />
              <SideItem id="skills" icon={<Zap size={18}/>} label="Skill Central" active={activeTab === 'skills'} onClick={() => setActiveTab('skills')} />
              <SideItem id="nodes" icon={<Cpu size={18}/>} label="Nodes & Settings" active={activeTab === 'nodes'} onClick={() => setActiveTab('nodes')} />
              <SideItem id="billing" icon={<CreditCard size={18}/>} label="Pro Upgrade" active={activeTab === 'billing'} onClick={() => setActiveTab('billing')} />
              
              <div className="pt-8 pb-2 px-2 text-[10px] font-bold text-white/20 uppercase tracking-[0.2em]">External</div>
              <a 
                href="https://mandev.site" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-gold hover:bg-white/5 transition-all duration-300 group"
              >
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center group-hover:scale-110 group-hover:bg-gold/10 transition-all">
                  <span className="text-xs font-black">M</span>
                </div>
                <span className="text-[13px] font-bold">Daniel's Portfolio</span>
              </a>
            </div>

        <div className="p-8 border-t border-white/5 space-y-6">
            <div className="hidden md:block">
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-gold mb-3">Sovereign Node</p>
                <div className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                    <div className="flex justify-between items-center text-[10px] font-bold">
                        <span className="opacity-40 uppercase">Latency</span>
                        <span className="text-emerald-500">24ms</span>
                    </div>
                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 w-[80%]" />
                    </div>
                </div>
            </div>
                  <button 
                onClick={signOut}
                className="w-full flex items-center justify-center md:justify-start gap-4 px-4 py-3 rounded-2xl hover:bg-white/5 transition-all text-white/30 hover:text-white"
            >
                <Loader2 size={18} />
                <span className="hidden md:block text-[11px] font-black uppercase tracking-widest">Sign Out</span>
            </button>
        </div>
      </aside>

      {/* MAIN VIEWPORT */}
      <main className="flex-1 flex flex-col min-w-0">
        
        {/* HEADER AREA */}
        <header className="h-24 border-b border-white/5 flex items-center justify-between px-12 shrink-0">
            <div className="flex items-center gap-4">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_#10b981]" />
                <h2 className="text-xs font-black uppercase tracking-[0.3em] opacity-40">User Node: <span className="text-white">{user.email}</span></h2>
            </div>
            <div className="flex items-center gap-6">
                <div className="hidden lg:flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/5 rounded-xl">
                    <span className="text-[9px] font-black uppercase tracking-widest opacity-30">Active Intelligence:</span>
                    <span className="text-[10px] font-black uppercase tracking-widest text-gold">{activeModel || "Llama 3.1"}</span>
                </div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-zinc-800 to-zinc-700 border border-white/10 shadow-xl" />
            </div>
        </header>

        {/* SCROLLABLE VIEW */}
        <div className="flex-1 overflow-y-auto p-12 scroll-smooth">
            <div className="max-w-5xl mx-auto">
                {activeTab === 'commander' && (
                    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <div className="space-y-4">
                            <h2 className="text-5xl md:text-7xl font-black tracking-tighter leading-[0.9]">
                                Commander <span className="bg-clip-text text-transparent bg-gradient-to-r from-gold via-yellow-400 to-gold/50 text-glow">Nexus.</span>
                            </h2>
                            <p className="max-w-xl text-white/40 font-bold leading-relaxed">Instrucciones directas al núcleo de JARVIS. Tu infraestructura, bajo tu control total y absoluto.</p>
                        </div>

                        {/* TERMINAL UI */}
                        <div className="bg-zinc-900/40 border border-white/5 rounded-[40px] p-10 space-y-8 backdrop-blur-3xl shadow-inner min-h-[400px] flex flex-col">
                            <div className="flex-1 space-y-6 overflow-y-auto pr-4 scrollbar-hide">
                                {responses.length === 0 && (
                                    <div className="h-full flex flex-col items-center justify-center opacity-10 space-y-4 py-20">
                                        <TerminalIcon size={64} />
                                        <p className="text-[10px] font-black uppercase tracking-[0.4em]">Awaiting Strategic Inputs</p>
                                    </div>
                                )}
                                {responses.map((r, i) => (
                                    <div key={i} className={`flex gap-6 animate-in slide-in-from-left-2 duration-300 ${r.type === 'user' ? 'opacity-40' : r.type === 'error' ? 'text-red-400' : 'text-white'}`}>
                                        <span className="shrink-0 font-black text-[10px] uppercase tracking-widest pt-1">{r.type === 'user' ? 'USR' : 'SYS'}</span>
                                        <div className="flex-1 py-1">
                                            <p className="text-[14px] leading-relaxed whitespace-pre-wrap font-medium">{r.text}</p>
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="flex gap-6 animate-pulse text-gold">
                                        <span className="shrink-0 font-black text-[10px] uppercase tracking-widest">LLM</span>
                                        <p className="text-[14px] leading-relaxed font-black uppercase tracking-widest">Processing Intelligence Stream...</p>
                                    </div>
                                )}
                            </div>

                            <div className="relative pt-8">
                                <div className="absolute inset-0 bg-gold/5 blur-3xl opacity-20" />
                                <div className="relative flex gap-4">
                                    <input 
                                        type="text" 
                                        placeholder="Strategic command..." 
                                        value={command}
                                        onChange={(e) => setCommand(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
                                        className="flex-1 bg-white/5 border border-white/10 rounded-2xl px-8 py-5 text-lg font-bold placeholder:text-white/10 outline-none focus:border-gold/40 transition-all shadow-2xl"
                                    />
                                    <button 
                                        onClick={handleExecute}
                                        className="px-10 bg-gold hover:bg-yellow-400 text-black font-black uppercase tracking-widest text-xs rounded-2xl transition-all shadow-[0_10px_20px_rgba(255,215,0,0.2)] active:scale-95"
                                    >
                                        Execute
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'skills' && (
                    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <div className="space-y-4">
                            <h2 className="text-5xl font-black tracking-tighter uppercase italic">Skill <span className="text-gold">Central</span></h2>
                            <p className="text-white/40 font-bold max-w-xl">Habilita o restringe las capacidades de JARVIS en tiempo real. Máxima soberanía, mínimo riesgo.</p>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {skills.map((skill) => (
                                <div key={skill.id} className="p-8 bg-zinc-900/40 border border-white/5 rounded-[32px] hover:border-white/10 transition-all space-y-6">
                                    <div className="flex justify-between items-start">
                                        <h3 className="text-lg font-black uppercase tracking-tight">{skill.id.replace('_', ' ')}</h3>
                                        <div 
                                            onClick={() => toggleSkill(skill.id, skill.enabled)}
                                            className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${skill.enabled ? 'bg-gold' : 'bg-white/10'}`}
                                        >
                                            <div className={`w-4 h-4 bg-black rounded-full transition-transform ${skill.enabled ? 'translate-x-6' : 'translate-x-0'}`} />
                                        </div>
                                    </div>
                                    <p className="text-xs text-white/30 font-bold leading-relaxed">Controla el módulo de {skill.id} para permitir ejecuciones de herramientas externas.</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'knowledge' && (
                    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <div className="space-y-4 text-center py-20">
                            <div className="w-24 h-24 bg-white/5 border border-white/5 rounded-[32px] flex items-center justify-center mx-auto text-gold/20 mb-8 border-dashed">
                                <ShieldCheck size={48} />
                            </div>
                            <h2 className="text-4xl font-black tracking-tighter uppercase">Sovereign Data Cluster</h2>
                            <p className="text-white/30 font-bold max-w-md mx-auto">Sube documentos para alimentar la base de conocimiento local de JARVIS (RAG).</p>
                            <div className="pt-8">
                                <label className="inline-block px-12 py-5 bg-white text-black font-black uppercase tracking-widest text-[10px] rounded-2xl cursor-pointer hover:bg-gold transition-all shadow-xl">
                                    Upload Knowledge Base
                                    <input type="file" className="hidden" />
                                </label>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'nodes' && (
                    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <div className="space-y-8">
                            <h3 className="text-2xl font-black uppercase tracking-tighter">Model & Inference</h3>
                            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 mb-6">
                  <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-gold animate-pulse" />
                    Sovereign Node Configuration
                  </h3>
                  <p className="text-sm text-white/40 mb-6">
                    By default, ZODIT connects to our managed neural node. To use your own local JARVIS, enter your Gateway URL below.
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest block mb-2">Local Gateway URL</label>
                      <div className="flex gap-2">
                        <input 
                          type="text" 
                          value={customNodeUrl}
                          onChange={(e) => {
                            const val = e.target.value;
                            setCustomNodeUrl(val);
                            localStorage.setItem('zodit_custom_gateway', val);
                          }}
                          placeholder="e.g. https://zodit-gateway.mandev.site"
                          className="flex-1 bg-black border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-gold/50 transition-all font-mono"
                        />
                        <button 
                          onClick={() => {
                            setCustomNodeUrl('');
                            localStorage.removeItem('zodit_custom_gateway');
                            window.location.reload();
                          }}
                          className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-[10px] font-bold uppercase transition-all"
                        >
                          Reset Default
                        </button>
                      </div>
                      <p className="mt-2 text-[10px] text-white/20 italic">
                        Leave empty to use the shared managed infrastructure.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="p-10 bg-zinc-900/40 border border-white/5 rounded-[40px] space-y-6">
                                    <p className="text-[10px] font-black uppercase tracking-widest text-gold opacity-60">Active Intelligence Model</p>
                                    <select 
                                        className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-sm font-bold appearance-none outline-none focus:border-gold/30"
                                        value={activeModel}
                                        onChange={(e) => switchModel(e.target.value)}
                                    >
                                        <option value="">Default Model</option>
                                        {models.map(m => (
                                            <option key={m.name} value={m.name}>{m.name}</option>
                                        ))}
                                    </select>
                                    <p className="text-[10px] font-bold text-white/20">Tu PC local procesa la inferencia mediante Ollama.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
      </main>
    </div>
  );
}

function SideItem({ icon, label, active, onClick }: { id?: string, icon: any, label: string, active: boolean, onClick: () => void }) {
    return (
        <button 
            onClick={onClick}
            className={`w-full flex items-center justify-center md:justify-start gap-4 px-6 py-4 rounded-2xl transition-all group ${
                active ? 'bg-gold text-black shadow-lg' : 'text-white/30 hover:bg-white/5 hover:text-white'
            }`}
        >
            <span className={`transition-transform duration-500 ${active ? 'scale-110' : 'group-hover:scale-110'}`}>{icon}</span>
            <span className="hidden md:block text-[11px] font-black uppercase tracking-[0.2em]">{label}</span>
            {active && <div className="hidden md:block ml-auto w-1 h-1 bg-black rounded-full" />}
        </button>
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

