import { ShieldCheck } from 'lucide-react';

type PublicHeaderProps = {
  onLogin: () => void;
};

export function PublicHeader({ onLogin }: PublicHeaderProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-30 border-b border-white/10 bg-ink/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-300/25 bg-cyan-300/10 text-cyan-200">
            <ShieldCheck size={20} />
          </div>
          <span className="text-sm font-semibold uppercase tracking-[0.18em] text-white">InfoCheck ID</span>
        </div>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <a href="#platform" className="transition hover:text-white">Platform</a>
          <a href="#monitoring" className="transition hover:text-white">Monitoring</a>
          <a href="#ocr" className="transition hover:text-white">OCR</a>
        </nav>
        <button
          type="button"
          onClick={onLogin}
          className="rounded-lg border border-cyan-300/30 px-4 py-2 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-300/10"
        >
          Login
        </button>
      </div>
    </header>
  );
}
