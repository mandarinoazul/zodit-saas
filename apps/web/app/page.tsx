export default function Home() {
  return (
    <div className="flex-1 container mx-auto px-4 md:px-8 py-12 md:py-20">
      <div className="max-w-5xl mx-auto space-y-16">
        
        {/* Hero Section */}
        <div className="space-y-6 text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gold/10 border border-gold/20 text-[10px] uppercase tracking-widest font-bold text-gold mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gold"></span>
            </span>
            Neural Gateway Active
          </div>
          <h2 className="text-5xl md:text-7xl font-black tracking-tighter leading-[0.9]">
            The World's First <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-gold via-yellow-400 to-gold/50">Private Intelligence.</span>
          </h2>
          <p className="text-white/50 text-xl max-w-2xl font-medium">
            Take full control of your digital life. Automate PC tasks, WhatsApp flows, and knowledge retrieval while keeping your data strictly local.
          </p>
        </div>

        {/* Skill Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <SkillCard 
            title="Local Execution" 
            desc="Control your Windows machine with natural language instructions."
            icon="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
          />
          <SkillCard 
            title="WhatsApp Bridge" 
            desc="Automate conversations and analyze chats with local privacy."
            icon="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-7.6 8.38 8.38 0 0 1 3.8.9L21 3.5z"
          />
          <SkillCard 
            title="Sovereign Memory" 
            desc="Deep RAG analysis on your local documents. Zero cloud leaks."
            icon="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
          />
        </div>

        {/* Command Interface */}
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-gold/20 to-transparent rounded-[32px] blur-xl opacity-50 group-hover:opacity-100 transition duration-500" />
          <div className="relative bg-zinc-900/40 border border-white/10 backdrop-blur-2xl rounded-[32px] p-8 md:p-12 space-y-8">
            <div className="flex justify-between items-center">
              <h3 className="text-2xl font-black tracking-tight uppercase">Neural Command</h3>
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-white/5" />
                <div className="w-3 h-3 rounded-full bg-white/5" />
                <div className="w-3 h-3 rounded-full bg-white/5" />
              </div>
            </div>
            <div className="relative flex flex-col md:flex-row gap-4">
              <input 
                type="text" 
                placeholder="Ask Zodit to perform a task..." 
                className="flex-1 bg-black/50 border border-white/10 rounded-2xl px-6 py-4 text-lg focus:outline-none focus:border-gold/50 transition-all font-medium placeholder:text-white/20"
              />
              <button className="bg-gradient-to-br from-gold to-yellow-600 text-black font-black uppercase tracking-widest text-sm px-10 py-4 rounded-2xl shadow-[0_10px_20px_rgba(255,215,0,0.2)] hover:shadow-[0_15px_30px_rgba(255,215,0,0.3)] hover:-translate-y-0.5 active:translate-y-0 transition-all">
                Execute
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SkillCard({ title, desc, icon }: { title: string; desc: string; icon: string }) {
  return (
    <div className="group relative bg-zinc-900/30 border border-white/5 p-8 rounded-[24px] hover:border-gold/30 transition-all cursor-pointer overflow-hidden">
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-30 group-hover:rotate-12 transition-all">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gold">
          <path d={icon} />
        </svg>
      </div>
      <div className="space-y-4">
        <div className="w-10 h-1 rounded-full bg-gold/30 group-hover:w-16 group-hover:bg-gold transition-all duration-500" />
        <h3 className="text-xl font-bold tracking-tight">{title}</h3>
        <p className="text-sm text-white/40 font-medium leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
