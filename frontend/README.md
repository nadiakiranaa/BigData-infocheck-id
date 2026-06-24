# InfoCheck ID Frontend

Dashboard React + TypeScript + Tailwind CSS untuk monitoring deteksi hoaks dan penipuan real-time.

## Struktur

```text
src/
├── components/
│   ├── dashboard/     # Stat cards, live feed table, OCR test panel
│   ├── layout/        # Public header dan dashboard sidebar
│   └── ui/            # Komponen UI kecil reusable
├── data/              # Dummy data untuk preview dashboard
├── pages/             # Landing page dan dashboard page
├── types/             # TypeScript domain types
├── App.tsx
└── main.tsx
```

## Menjalankan

```bash
npm install
npm run dev
```

Klik tombol `Login to Monitor Dashboard` pada landing page untuk membuka dashboard dummy.
