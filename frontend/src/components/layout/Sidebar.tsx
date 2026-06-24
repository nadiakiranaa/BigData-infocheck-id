import { Activity, Database, FileScan, LayoutDashboard, ShieldCheck } from 'lucide-react';
import type { DashboardTab } from '../../types/monitoring';

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'live-feed', label: 'Live Feed', icon: Activity },
  { id: 'scam-db', label: 'Scam DB', icon: Database },
  { id: 'ocr-test', label: 'OCR Test', icon: FileScan },
];

type SidebarProps = {
  activeTab: DashboardTab;
  onTabChange: (tab: DashboardTab) => void;
};

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <aside className="hidden min-h-screen w-72 border-r border-slate-200 bg-white px-5 py-6 dark:border-white/10 dark:bg-[#080d19]/95 lg:block">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-cyan-300/25 bg-cyan-300/10 text-cyan-200 shadow-glow">
          <ShieldCheck size={24} />
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-950 dark:text-white">InfoCheck</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Threat Monitor</p>
        </div>
      </div>

      <nav className="mt-10 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              type="button"
              onClick={() => onTabChange(item.id as DashboardTab)}
              className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm font-medium transition ${
                activeTab === item.id
                  ? 'border border-cyan-300/40 bg-cyan-100 text-cyan-700 dark:border-cyan-300/25 dark:bg-cyan-300/10 dark:text-cyan-100'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white'
              }`}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="mt-10 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/[0.03]">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Pipeline Health</p>
        <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
          Menggambarkan beban pipeline real-time dari kapasitas aman saat ini.
        </p>
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-slate-700 dark:text-slate-300">Kafka Throughput</span>
          <span className="font-semibold text-cyan-700 dark:text-cyan-200">82%</span>
        </div>
        <div className="mt-3 h-2 rounded-full bg-slate-200 dark:bg-slate-800">
          <div className="h-2 w-[82%] rounded-full bg-cyan-500 dark:bg-cyan-300" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
          <div>
            <p className="text-slate-500 dark:text-slate-400">Uptime</p>
            <p className="mt-1 font-semibold text-emerald-600 dark:text-emerald-300">99.7%</p>
          </div>
          <div>
            <p className="text-slate-500 dark:text-slate-400">Latency</p>
            <p className="mt-1 font-semibold text-slate-950 dark:text-white">184ms</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
