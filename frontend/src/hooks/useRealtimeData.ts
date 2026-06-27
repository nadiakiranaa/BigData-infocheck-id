import { AlertTriangle, DatabaseZap, MessageSquareText } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { FeedItem, ScamRecord, StatCardData } from '../types/monitoring';

const API_BASE_URL = 'http://localhost:8001/api';

export function useRealtimeData() {
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [scamRecords, setScamRecords] = useState<ScamRecord[]>([]);
  const [stats, setStats] = useState<StatCardData[]>([]);
  const [hourlyVolume, setHourlyVolume] = useState<{label: string, value: number}[]>([]);
  const [riskScatter, setRiskScatter] = useState<{label: string, value: number}[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        const [feedRes, statsRes, scamRes] = await Promise.all([
          fetch(`${API_BASE_URL}/live-feed`),
          fetch(`${API_BASE_URL}/stats`),
          fetch(`${API_BASE_URL}/scam-db`)
        ]);

        if (!feedRes.ok || !statsRes.ok || !scamRes.ok) {
          throw new Error('Failed to fetch data from API Bridge');
        }

        const feedData = await feedRes.json();
        const statsData = await statsRes.json();
        const scamData = await scamRes.json();

        if (isMounted) {
          // 1. Format Stats
          const formattedStats: StatCardData[] = [
            {
              label: 'Total Pesan',
              value: statsData.total_messages_today.toLocaleString('id-ID'),
              trend: 'Data real-time Kafka',
              tone: 'cyan',
              icon: MessageSquareText,
            },
            {
              label: 'Hoaks Terdeteksi',
              value: statsData.hoax_detected_today.toLocaleString('id-ID'),
              trend: 'Model IndoBERT v2',
              tone: 'rose',
              icon: AlertTriangle,
            },
            {
              label: 'Penipuan Terdeteksi',
              value: statsData.scam_detected_today.toLocaleString('id-ID'),
              trend: 'Menunggu review manual',
              tone: 'amber',
              icon: DatabaseZap,
            },
          ];
          setStats(formattedStats);
          setHourlyVolume(statsData.hourly_volume || []);
          setRiskScatter(statsData.risk_scatter || []);

          // 2. Format Live Feed
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const formattedFeed: FeedItem[] = feedData.map((item: any) => {
            // Extract time from timestamp safely
            let timeString = '-';
            if (item.timestamp) {
              try {
                const date = new Date(item.timestamp);
                if (!isNaN(date.getTime())) {
                  timeString = date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }
              } catch (e) {
                // Ignore parsing errors
              }
            }
            
            // Map label to FeedStatus ('valid', 'hoaks', 'penipuan', 'netral')
            let status: FeedItem['status'] = 'Review';
            const labelLower = (item.label || '').toLowerCase();
            if (labelLower === 'valid') status = 'Valid';
            else if (labelLower === 'hoaks') status = 'Hoaks';
            else if (labelLower === 'penipuan') status = 'Penipuan';
            else if (labelLower === 'netral') status = 'Netral';

            return {
              id: item.id,
              time: timeString,
              source: item.source || item.source_type || 'Unknown',
              snippet: item.text_snippet || '',
              status,
              confidence: Math.round(item.confidence || 0),
              url: item.url
            };
          });
          setFeedItems(formattedFeed);

          // 3. Format Scam Records
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const formattedScam: ScamRecord[] = scamData.map((record: any) => {
            const date = new Date(record.updated_at);
            const timeString = date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });

            let type: ScamRecord['type'] = 'Nomor Rekening';
            if (record.scam_type && record.scam_type.toLowerCase().includes('phone')) {
              type = 'Nomor Telepon';
            }

            let status: ScamRecord['status'] = 'Review';
            const statusLower = (record.status || '').toLowerCase();
            if (statusLower === 'aktif' || statusLower === 'active') status = 'Aktif';
            else if (statusLower === 'selesai' || statusLower === 'resolved') status = 'Selesai';

            return {
              id: record.id,
              type,
              value: record.value || '-',
              owner: record.owner_name || 'Tidak diketahui',
              source: record.source || 'Laporan Pengguna',
              reports: record.report_count || 0,
              status,
              updatedAt: timeString,
            };
          });
          setScamRecords(formattedScam);
          
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Error fetching realtime data:", error);
        // Fallback to empty state on error but don't show loading forever
        if (isMounted) setIsLoading(false);
      }
    };

    // Fetch immediately
    fetchData();

    // Poll every 3 seconds
    const interval = setInterval(fetchData, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return { feedItems, scamRecords, stats, hourlyVolume, riskScatter, isLoading };
}
