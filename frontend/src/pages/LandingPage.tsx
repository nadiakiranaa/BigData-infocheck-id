import { ArrowRight, Eye, RadioTower, ShieldAlert } from 'lucide-react';
import { PublicHeader } from '../components/layout/PublicHeader';

type LandingPageProps = {
  onLogin: () => void;
};

export function LandingPage({ onLogin }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-ink text-white">
      <PublicHeader onLogin={onLogin} />

      <main className="relative overflow-hidden pt-16">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(34,211,238,0.16),transparent_34%),radial-gradient(circle_at_80%_10%,rgba(251,113,133,0.13),transparent_30%),linear-gradient(180deg,rgba(13,20,36,0.3),rgba(6,9,20,1))]" />
        <div className="absolute inset-x-0 top-16 h-px bg-gradient-to-r from-transparent via-cyan-300/50 to-transparent" />

        <section className="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[1fr_0.9fr]">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-sm font-medium text-cyan-100">
              <RadioTower size={16} />
              Real-time hoax and scam detection
            </div>
            <h1 className="mt-7 max-w-4xl text-5xl font-semibold leading-tight text-white sm:text-6xl lg:text-7xl">
              InfoCheck ID
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              Sistem pusat pemantauan untuk mendeteksi hoaks dan penipuan dari pesan Telegram, RSS berita, dan screenshot percakapan secara real-time.
            </p>
            <button
              type="button"
              onClick={onLogin}
              className="mt-9 inline-flex items-center gap-3 rounded-lg bg-cyan-300 px-6 py-4 text-base font-semibold text-slate-950 shadow-glow transition hover:bg-cyan-200"
            >
              Login to Monitor Dashboard
              <ArrowRight size={19} />
            </button>
          </div>

          <div className="relative min-h-[470px]" id="platform">
            <div className="absolute inset-0 rounded-lg border border-cyan-300/20 bg-panel/80 shadow-2xl shadow-cyan-950/30 backdrop-blur">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
                </div>
                <span className="font-mono text-xs text-slate-500">monitor.infocheck.id</span>
              </div>
              <div className="p-5">
                <div className="grid gap-3 sm:grid-cols-3">
                  {['128K pesan', '2.9K hoaks', '743 scam'].map((item) => (
                    <div key={item} className="rounded-lg border border-white/10 bg-white/[0.04] p-4">
                      <p className="text-sm text-slate-400">{item.split(' ')[1]}</p>
                      <p className="mt-2 text-2xl font-semibold text-white">{item.split(' ')[0]}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-5 space-y-3" id="monitoring">
                  {[
                    ['09:47:12', 'Scam', 'Klaim bantuan pemerintah melalui link palsu'],
                    ['09:46:38', 'Hoaks', 'Narasi lama kembali viral dengan lokasi baru'],
                    ['09:45:21', 'Aman', 'Artikel resmi kanal berita nasional'],
                  ].map(([time, status, text]) => (
                    <div key={time} className="grid grid-cols-[72px_76px_1fr] items-center gap-3 rounded-lg border border-white/10 bg-ink/60 p-3 text-sm">
                      <span className="font-mono text-xs text-cyan-100">{time}</span>
                      <span className="text-slate-200">{status}</span>
                      <span className="truncate text-slate-400">{text}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-lg border border-amber-300/20 bg-amber-300/10 p-4">
                  <div className="flex items-center gap-3">
                    <ShieldAlert className="text-amber-100" size={21} />
                    <div>
                      <p className="font-semibold text-amber-100">Threat cluster detected</p>
                      <p className="mt-1 text-sm text-amber-100/70">89 tautan mencurigakan dari kanal pesan publik.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-5 left-8 right-8 rounded-lg border border-cyan-300/20 bg-cyan-300/10 p-4 backdrop-blur">
              <div className="flex items-center gap-3 text-cyan-100">
                <Eye size={18} />
                <span className="text-sm font-semibold">Model confidence updated every stream event</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
