import type { ChartPoint } from '../../types/monitoring';
import { SectionHeader } from '../ui/SectionHeader';

type ChartsPanelProps = {
  hourlyVolume: ChartPoint[];
  riskScatter: ChartPoint[];
};

const pieColors = ['#06b6d4', '#f43f5e', '#f59e0b', '#10b981', '#6366f1', '#8b5cf6'];

export function ChartsPanel({ hourlyVolume, riskScatter }: ChartsPanelProps) {
  const maxVolume = Math.max(...hourlyVolume.map((item) => item.value));
  const totalRisk = riskScatter.reduce((total, item) => total + item.value, 0);
  let currentPercent = 0;
  const pieGradient = riskScatter
    .map((item, index) => {
      const start = currentPercent;
      const end = start + (item.value / totalRisk) * 100;
      currentPercent = end;
      return `${pieColors[index % pieColors.length]} ${start}% ${end}%`;
    })
    .join(', ');

  return (
    <section className="grid gap-5 xl:grid-cols-2">
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-panel/90">
        <SectionHeader
          title="Volume Pesan per Jam"
          description="Grafik batang ini memperlihatkan beban pesan yang diproses pipeline hari ini."
        />
        <div className="mt-6 flex h-64 items-end gap-3 border-b border-l border-slate-200 px-2 pb-2 dark:border-white/10">
          {hourlyVolume.map((item) => (
            <div key={item.label} className="flex h-full flex-1 flex-col justify-end gap-2">
              <div
                className="min-h-3 rounded-t bg-cyan-500 transition dark:bg-cyan-300"
                style={{ height: `${(item.value / maxVolume) * 100}%` }}
                title={`${item.value} pesan`}
              />
              <span className="text-center font-mono text-xs text-slate-500 dark:text-slate-400">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-panel/90">
        <SectionHeader
          title="Sebaran Risiko Sumber"
          description="Grafik lingkaran memperlihatkan kontribusi risiko dari setiap sumber stream."
        />
        <div className="mt-6 grid gap-6 md:grid-cols-[240px_1fr] md:items-center">
          <div className="relative mx-auto h-56 w-56 rounded-full shadow-inner" style={{ background: `conic-gradient(${pieGradient})` }}>
            <div className="absolute inset-10 flex flex-col items-center justify-center rounded-full border border-slate-200 bg-white text-center dark:border-white/10 dark:bg-panel">
              <span className="text-xs uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Total Risiko</span>
              <span className="mt-2 text-3xl font-semibold text-slate-950 dark:text-white">{totalRisk}</span>
              <span className="mt-1 text-xs text-slate-500 dark:text-slate-400">score</span>
            </div>
          </div>
          <div className="space-y-3">
            {riskScatter.map((item, index) => {
              const percentage = Math.round((item.value / totalRisk) * 100);
              return (
                <div key={item.label} className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-ink/50">
                  <div className="flex items-center gap-3">
                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: pieColors[index % pieColors.length] }} />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{item.label}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-950 dark:text-white">{percentage}%</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.value} score</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
