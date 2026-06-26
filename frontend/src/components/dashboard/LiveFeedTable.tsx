import type { FeedItem } from '../../types/monitoring';
import { Badge } from '../ui/Badge';
import { SectionHeader } from '../ui/SectionHeader';

type LiveFeedTableProps = {
  items: FeedItem[];
  query?: string;
};

export function LiveFeedTable({ items, query = '' }: LiveFeedTableProps) {
  const normalizedQuery = query.trim().toLowerCase();
  const filteredItems = normalizedQuery
    ? items.filter((item) =>
        [item.time, item.source, item.snippet, item.status, item.confidence]
          .join(' ')
          .toLowerCase()
          .includes(normalizedQuery),
      )
    : items;

  return (
    <section className="rounded-lg border border-slate-200 bg-white dark:border-white/10 dark:bg-panel/90">
      <div className="flex flex-col gap-4 border-b border-slate-200 p-5 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
        <SectionHeader
          title="Live Feed Stream"
          description="Pantauan pesan masuk dari kanal RSS dan Telegram dengan klasifikasi model real-time."
        />
        <div className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-300/30 bg-emerald-300/10 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-200">
          <span className="h-2 w-2 rounded-full bg-emerald-300" />
          Live
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-white/10">
          <thead className="bg-slate-50 text-xs uppercase tracking-[0.16em] text-slate-500 dark:bg-white/[0.03]">
            <tr>
              <th className="px-5 py-4 font-semibold">Waktu</th>
              <th className="px-5 py-4 font-semibold">Sumber</th>
              <th className="px-5 py-4 font-semibold">Cuplikan Teks</th>
              <th className="px-5 py-4 font-semibold">Status</th>
              <th className="px-5 py-4 font-semibold">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-white/10">
            {filteredItems.map((item) => (
              <tr key={item.id} className="transition hover:bg-slate-50 dark:hover:bg-white/[0.03]">
                <td className="whitespace-nowrap px-5 py-4 font-mono text-xs text-cyan-700 dark:text-cyan-100">{item.time}</td>
                <td className="whitespace-nowrap px-5 py-4 text-slate-700 dark:text-slate-300">{item.source}</td>
                <td className="min-w-[320px] px-5 py-4 text-slate-500 dark:text-slate-400">
                  {item.url ? (
                    <a href={item.url} target="_blank" rel="noreferrer" className="hover:text-cyan-600 hover:underline dark:hover:text-cyan-400 transition-colors">
                      {item.snippet}
                    </a>
                  ) : (
                    item.snippet
                  )}
                </td>
                <td className="whitespace-nowrap px-5 py-4">
                  <Badge status={item.status} />
                </td>
                <td className="whitespace-nowrap px-5 py-4 text-slate-700 dark:text-slate-300">{item.confidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
