type SectionHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
};

export function SectionHeader({ eyebrow, title, description }: SectionHeaderProps) {
  return (
    <div>
      {eyebrow ? (
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-600 dark:text-cyan-200/80">{eyebrow}</p>
      ) : null}
      <h2 className="text-xl font-semibold text-slate-950 dark:text-white">{title}</h2>
      {description ? <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p> : null}
    </div>
  );
}
