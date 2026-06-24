import { useCallback, useMemo, useState } from 'react';
import { FileImage, ScanText, UploadCloud } from 'lucide-react';
import { SectionHeader } from '../ui/SectionHeader';

type AnalysisResult = {
  text: string;
  status: 'Scam Terdeteksi' | 'Perlu Review';
};

export function OcrTestPanel() {
  const [fileName, setFileName] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const helperText = useMemo(() => {
    if (fileName) {
      return fileName;
    }

    return 'PNG, JPG, atau screenshot percakapan';
  }, [fileName]);

  const setUploadedFile = useCallback((file?: File) => {
    if (!file) {
      return;
    }

    setFileName(file.name);
    setResult(null);
  }, []);

  const handleAnalyze = () => {
    setResult({
      text: 'Selamat! Anda terpilih menerima bantuan Rp5.000.000. Klik tautan bit.ly/claim-bansos untuk verifikasi rekening.',
      status: fileName ? 'Scam Terdeteksi' : 'Perlu Review',
    });
  };

  return (
    <section id="ocr" className="rounded-lg border border-slate-200 bg-white p-5 dark:border-white/10 dark:bg-panel/90">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <SectionHeader
          title="OCR Test"
          description="Uji screenshot pesan mencurigakan sebelum masuk ke database investigasi."
        />
        <button
          type="button"
          onClick={handleAnalyze}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-cyan-600 dark:bg-cyan-300 dark:text-slate-950 dark:hover:bg-cyan-200"
        >
          <ScanText size={17} />
          Analisis Gambar
        </button>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_0.85fr]">
        <label
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            setUploadedFile(event.dataTransfer.files[0]);
          }}
          className={`flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center transition ${
            isDragging
              ? 'border-cyan-400 bg-cyan-100 dark:border-cyan-200 dark:bg-cyan-300/10'
              : 'border-slate-300 bg-slate-50 hover:border-cyan-400 hover:bg-cyan-50 dark:border-slate-600 dark:bg-white/[0.03] dark:hover:border-cyan-300/50 dark:hover:bg-cyan-300/5'
          }`}
        >
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="sr-only"
            onChange={(event) => setUploadedFile(event.target.files?.[0])}
          />
          <div className="flex h-16 w-16 items-center justify-center rounded-lg border border-cyan-300/30 bg-cyan-100 text-cyan-700 dark:bg-cyan-300/10 dark:text-cyan-100">
            {fileName ? <FileImage size={30} /> : <UploadCloud size={30} />}
          </div>
          <p className="mt-5 text-base font-semibold text-slate-950 dark:text-white">Tarik screenshot ke sini</p>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{helperText}</p>
        </label>

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-ink/60">
          <p className="text-sm font-semibold text-slate-950 dark:text-white">Hasil Analisis</p>
          {result ? (
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">OCR Text</p>
                <p className="mt-2 rounded-lg border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300">
                  {result.text}
                </p>
              </div>
              <div className="rounded-lg border border-amber-300/25 bg-amber-300/10 p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-amber-100/70">Status</p>
                <p className="mt-1 text-lg font-semibold text-amber-100">{result.status}</p>
              </div>
            </div>
          ) : (
            <div className="mt-4 flex min-h-52 items-center justify-center rounded-lg border border-slate-200 bg-white p-6 text-center text-sm leading-6 text-slate-500 dark:border-white/10 dark:bg-white/[0.02]">
              Hasil teks OCR dan status penipuan akan tampil setelah gambar dianalisis.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
