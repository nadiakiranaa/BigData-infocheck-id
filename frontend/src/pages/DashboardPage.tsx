import { Bell, Moon, Search, Sun } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { ChartsPanel } from '../components/dashboard/ChartsPanel';
import { LiveFeedTable } from '../components/dashboard/LiveFeedTable';
import { OcrTestPanel } from '../components/dashboard/OcrTestPanel';
import { ScamDbPanel } from '../components/dashboard/ScamDbPanel';
import { StatsGrid } from '../components/dashboard/StatsGrid';
import { Sidebar } from '../components/layout/Sidebar';
import { feedItems, hourlyVolume, notifications, riskScatter, scamRecords, stats } from '../data/dummyData';
import type { DashboardTab } from '../types/monitoring';

type DashboardPageProps = {
  onLogout: () => void;
};

export function DashboardPage({ onLogout }: DashboardPageProps) {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
    document.documentElement.style.colorScheme = isDarkMode ? 'dark' : 'light';
  }, [isDarkMode]);

  const activeTitle = useMemo(() => {
    const titles: Record<DashboardTab, string> = {
      overview: 'Overview',
      'live-feed': 'Live Feed',
      'scam-db': 'Scam DB',
      'ocr-test': 'OCR Test',
    };

    return titles[activeTab];
  }, [activeTab]);

  const renderContent = () => {
    if (activeTab === 'live-feed') {
      return <LiveFeedTable items={feedItems} query={searchQuery} />;
    }

    if (activeTab === 'scam-db') {
      return <ScamDbPanel records={scamRecords} query={searchQuery} />;
    }

    if (activeTab === 'ocr-test') {
      return <OcrTestPanel />;
    }

    return (
      <>
        <StatsGrid stats={stats} />
        <ChartsPanel hourlyVolume={hourlyVolume} riskScatter={riskScatter} />
        <LiveFeedTable items={feedItems.slice(0, 4)} query={searchQuery} />
      </>
    );
  };

  return (
    <div className={isDarkMode ? 'dark' : ''}>
    <div className="min-h-screen bg-slate-100 text-slate-950 dark:bg-ink dark:text-white">
      <div className="flex">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

        <main className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/85 px-5 py-4 backdrop-blur-xl dark:border-white/10 dark:bg-ink/85 sm:px-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Security Monitoring Dashboard</p>
                <h1 className="mt-1 text-2xl font-semibold text-slate-950 dark:text-white">{activeTitle}</h1>
              </div>
              <div className="flex items-center gap-3">
                <label className="hidden h-10 min-w-72 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-slate-500 dark:border-white/10 dark:bg-white/[0.03] sm:flex">
                  <Search size={17} />
                  <input
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Cari event, sumber, label..."
                    className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-200"
                  />
                </label>
                <button
                  type="button"
                  onClick={() => setIsDarkMode((value) => !value)}
                  className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
                  aria-label="Toggle theme"
                >
                  {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
                </button>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setIsNotificationsOpen((value) => !value)}
                    className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
                    aria-label="Open notifications"
                  >
                    <Bell size={18} />
                    <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500" />
                  </button>
                  {isNotificationsOpen ? (
                    <div className="absolute right-0 mt-3 w-80 rounded-lg border border-slate-200 bg-white p-3 shadow-xl dark:border-white/10 dark:bg-panel">
                      <p className="px-2 pb-2 text-sm font-semibold text-slate-950 dark:text-white">Notifikasi</p>
                      <div className="space-y-2">
                        {notifications.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            className="w-full rounded-lg p-3 text-left transition hover:bg-slate-50 dark:hover:bg-white/[0.04]"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.title}</p>
                              <span className="text-xs text-slate-500">{item.time}</span>
                            </div>
                            <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{item.description}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={onLogout}
                  className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 dark:border-white/10 dark:text-slate-200 dark:hover:bg-white/5"
                >
                  Logout
                </button>
              </div>
            </div>
          </header>

          <div className="space-y-6 px-5 py-6 sm:px-8">
            <label className="flex h-11 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-slate-500 dark:border-white/10 dark:bg-white/[0.03] sm:hidden">
              <Search size={17} />
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Cari data dashboard..."
                className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-200"
              />
            </label>
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
    </div>
  );
}
