import type { StatCardData } from '../../types/monitoring';
import { StatCard } from './StatCard';

type StatsGridProps = {
  stats: StatCardData[];
};

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <section className="grid gap-4 md:grid-cols-3">
      {stats.map((stat) => (
        <StatCard key={stat.label} stat={stat} />
      ))}
    </section>
  );
}
