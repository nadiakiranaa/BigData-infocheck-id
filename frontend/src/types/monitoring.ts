import type { LucideIcon } from 'lucide-react';

export type FeedStatus = 'Hoaks' | 'Scam' | 'Aman' | 'Review';
export type DashboardTab = 'overview' | 'live-feed' | 'scam-db' | 'ocr-test';

export type FeedItem = {
  id: string;
  time: string;
  source: string;
  snippet: string;
  status: FeedStatus;
  confidence: number;
};

export type StatCardData = {
  label: string;
  value: string;
  trend: string;
  tone: 'cyan' | 'rose' | 'amber';
  icon: LucideIcon;
};

export type ScamRecord = {
  id: string;
  type: 'Nomor Rekening' | 'Nomor Telepon';
  value: string;
  owner: string;
  source: string;
  reports: number;
  status: 'Aktif' | 'Review' | 'Selesai';
  updatedAt: string;
};

export type ChartPoint = {
  label: string;
  value: number;
};

export type NotificationItem = {
  id: string;
  title: string;
  description: string;
  time: string;
  severity: 'High' | 'Medium' | 'Info';
};
