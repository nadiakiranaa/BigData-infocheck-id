import { AlertTriangle, DatabaseZap, MessageSquareText } from 'lucide-react';
import type { ChartPoint, FeedItem, NotificationItem, ScamRecord, StatCardData } from '../types/monitoring';

export const stats: StatCardData[] = [
  {
    label: 'Total Pesan',
    value: '128.430',
    trend: '+12,8% dalam 24 jam',
    tone: 'cyan',
    icon: MessageSquareText,
  },
  {
    label: 'Hoaks Terdeteksi',
    value: '2.918',
    trend: '416 prioritas tinggi',
    tone: 'rose',
    icon: AlertTriangle,
  },
  {
    label: 'Penipuan Terdeteksi',
    value: '743',
    trend: '89 tautan diblokir',
    tone: 'amber',
    icon: DatabaseZap,
  },
];

export const feedItems: FeedItem[] = [
  {
    id: 'evt-1001',
    time: '09:47:12',
    source: 'Telegram - CekFakta',
    snippet: 'Klaim bantuan presiden Rp5 juta melalui tautan formulir tidak resmi...',
    status: 'Penipuan',
    confidence: 97,
  },
  {
    id: 'evt-1002',
    time: '09:46:38',
    source: 'RSS - TurnBackHoax',
    snippet: 'Narasi lama tentang penculikan anak kembali beredar dengan lokasi baru...',
    status: 'Hoaks',
    confidence: 94,
  },
  {
    id: 'evt-1003',
    time: '09:45:21',
    source: 'Telegram - Kompas.com',
    snippet: 'Artikel resmi mengenai kebijakan bantuan sosial dan kanal pengaduan...',
    status: 'Valid',
    confidence: 91,
  },
  {
    id: 'evt-1004',
    time: '09:44:59',
    source: 'RSS - Detik News',
    snippet: 'Klaim tentang investasi dari PT Pertamina (Persero) dengan profit harian...',
    status: 'Review',
    confidence: 68,
  },
  {
    id: 'evt-1005',
    time: '09:43:12',
    source: 'Telegram - CNBC Indonesia',
    snippet: 'Dapatkan kuota gratis 50GB Telkomsel edisi spesial lebaran klik link ini...',
    status: 'Penipuan',
    confidence: 96,
  },
  {
    id: 'evt-1006',
    time: '09:40:00',
    source: 'Telegram - Promo Bot',
    snippet: 'Promo KFC hari ini diskon 50% untuk pembelian via aplikasi resmi KFC...',
    status: 'Netral',
    confidence: 88,
  },
];

export const scamRecords: ScamRecord[] = [
  {
    id: 'scam-001',
    type: 'Nomor Rekening',
    value: '0147829931',
    owner: 'PT Bantuan Digital Nusantara',
    source: 'Telegram public report',
    reports: 42,
    status: 'Aktif',
    updatedAt: '09:10',
  },
  {
    id: 'scam-002',
    type: 'Nomor Telepon',
    value: '+6281212349988',
    owner: 'Admin Investasi Prioritas',
    source: 'RSS incident enrichment',
    reports: 18,
    status: 'Review',
    updatedAt: '08:55',
  },
  {
    id: 'scam-003',
    type: 'Nomor Rekening',
    value: '8821094432',
    owner: 'Komunitas Hadiah Digital',
    source: 'OCR screenshot',
    reports: 27,
    status: 'Aktif',
    updatedAt: '08:31',
  },
  {
    id: 'scam-004',
    type: 'Nomor Telepon',
    value: '+6285777001199',
    owner: 'CS Verifikasi Bansos',
    source: 'Telegram user report',
    reports: 9,
    status: 'Selesai',
    updatedAt: '07:42',
  },
];

export const hourlyVolume: ChartPoint[] = [
  { label: '06', value: 520 },
  { label: '07', value: 740 },
  { label: '08', value: 1180 },
  { label: '09', value: 1640 },
  { label: '10', value: 1370 },
  { label: '11', value: 1510 },
  { label: '12', value: 980 },
  { label: '13', value: 1260 },
];

export const riskScatter: ChartPoint[] = [
  { label: 'CekFakta', value: 92 },
  { label: 'RSS News', value: 68 },
  { label: 'Telegram', value: 97 },
  { label: 'Kompas', value: 31 },
  { label: 'Detik', value: 54 },
  { label: 'CNBC', value: 84 },
];

export const notifications: NotificationItem[] = [
  {
    id: 'notif-001',
    title: 'Lonjakan scam bansos',
    description: '89 tautan pendek muncul dari 3 kanal Telegram dalam 30 menit.',
    time: '2 menit lalu',
    severity: 'High',
  },
  {
    id: 'notif-002',
    title: 'Scam DB diperbarui',
    description: '3 nomor rekening baru masuk dari hasil OCR screenshot.',
    time: '12 menit lalu',
    severity: 'Medium',
  },
  {
    id: 'notif-003',
    title: 'Kafka stream stabil',
    description: 'Throughput rata-rata 82% dari kapasitas monitor saat ini.',
    time: '25 menit lalu',
    severity: 'Info',
  },
];
