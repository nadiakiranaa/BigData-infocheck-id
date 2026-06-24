import { Plus, ShieldAlert } from 'lucide-react';
import type { ScamRecord } from '../../types/monitoring';
import { SectionHeader } from '../ui/SectionHeader';

const statusClass: Record<ScamRecord['status'], string> = {
  Aktif: 'border-rose-300/40 bg-rose-500/10 text-rose-600 dark:text-rose-100',
  Review: 'border-amber-300/40 bg-amber-400/10 text-amber-700 dark:text-amber-100',
  Selesai: 'border-emerald-300/40 bg-emerald-400/10 text-emerald-700 dark:text-emerald-100',
};

type ScamDbPanelProps = {
  records: ScamRecord[];
  query: string;
};

export function ScamDbPanel({ records, query }: ScamDbPanelProps) {
  const normalizedQuery = query.trim().toLowerCase();
  const filteredRecords = normalizedQuery
    ? records.filter((record) =>
        [record.type, record.value, record.owner, record.source, record.status]
          .join(' ')
          .toLowerCase()
          .includes(normalizedQuery),
      )
    : records;

  return (
    <section className="rounded-lg border border-slate-200 bg-white dark:border-white/10 dark:bg-panel/90">
      <div className="flex flex-col gap-4 border-b border-slate-200 p-5 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
        <SectionHeader
          title="Scam Database"
          description="Database indikator penipuan dari laporan Telegram, RSS enrichment, dan hasil OCR."
        />
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-600 dark:bg-cyan-300 dark:text-slate-950 dark:hover:bg-cyan-200"
        >
          <Plus size={17} />
          Tambah Data
        </button>
      </div>

      <div className="grid gap-4 p-5 md:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-ink/50">
          <p className="text-sm text-slate-500 dark:text-slate-400">Indikator Aktif</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
            {records.filter((record) => record.status === 'Aktif').length}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-ink/50">
          <p className="text-sm text-slate-500 dark:text-slate-400">Total Laporan</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
            {records.reduce((total, record) => total + record.reports, 0)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-ink/50">
          <p className="text-sm text-slate-500 dark:text-slate-400">Perlu Review</p>
          <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
            {records.filter((record) => record.status === 'Review').length}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm dark:divide-white/10">
          <thead className="bg-slate-50 text-xs uppercase tracking-[0.16em] text-slate-500 dark:bg-white/[0.03]">
            <tr>
              <th className="px-5 py-4 font-semibold">Tipe</th>
              <th className="px-5 py-4 font-semibold">Nomor</th>
              <th className="px-5 py-4 font-semibold">Nama/Label</th>
              <th className="px-5 py-4 font-semibold">Sumber</th>
              <th className="px-5 py-4 font-semibold">Laporan</th>
              <th className="px-5 py-4 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-white/10">
            {filteredRecords.map((record) => (
              <tr key={record.id} className="transition hover:bg-slate-50 dark:hover:bg-white/[0.03]">
                <td className="whitespace-nowrap px-5 py-4 text-slate-700 dark:text-slate-300">{record.type}</td>
                <td className="whitespace-nowrap px-5 py-4 font-mono text-slate-950 dark:text-cyan-100">{record.value}</td>
                <td className="px-5 py-4 text-slate-700 dark:text-slate-300">{record.owner}</td>
                <td className="px-5 py-4 text-slate-500 dark:text-slate-400">{record.source}</td>
                <td className="whitespace-nowrap px-5 py-4 text-slate-700 dark:text-slate-300">{record.reports}</td>
                <td className="whitespace-nowrap px-5 py-4">
                  <span className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClass[record.status]}`}>
                    <ShieldAlert size={13} />
                    {record.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
