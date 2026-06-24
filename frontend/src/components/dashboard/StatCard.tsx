import type { StatCardData } from '../../types/monitoring';

const toneClass: Record<StatCardData['tone'], string> = {
  cyan: 'border-cyan-300/30 bg-cyan-100 text-cyan-700 dark:bg-cyan-300/10 dark:text-cyan-100',
  rose: 'border-rose-300/30 bg-rose-100 text-rose-700 dark:bg-rose-400/10 dark:text-rose-100',
  amber: 'border-amber-300/40 bg-amber-100 text-amber-700 dark:bg-amber-300/10 dark:text-amber-100',
};

type StatCardProps = {
  stat: StatCardData;
};

export function StatCard({ stat }: StatCardProps) {
  const Icon = stat.icon;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-panel/90 dark:shadow-2xl dark:shadow-black/20">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">{stat.label}</p>
          <p className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{stat.value}</p>
        </div>
        <div className={`flex h-12 w-12 items-center justify-center rounded-lg border ${toneClass[stat.tone]}`}>
          <Icon size={23} />
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">{stat.trend}</p>
    </article>
  );
}
