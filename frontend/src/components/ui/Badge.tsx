import type { FeedStatus } from '../../types/monitoring';

const statusClass: Record<FeedStatus, string> = {
  Aman: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-700 dark:text-emerald-200',
  Hoaks: 'border-rose-400/30 bg-rose-500/10 text-rose-700 dark:text-rose-200',
  Scam: 'border-amber-300/40 bg-amber-400/10 text-amber-700 dark:text-amber-100',
  Review: 'border-sky-300/35 bg-sky-400/10 text-sky-700 dark:text-sky-100',
};

type BadgeProps = {
  status: FeedStatus;
};

export function Badge({ status }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClass[status]}`}>
      {status}
    </span>
  );
}
