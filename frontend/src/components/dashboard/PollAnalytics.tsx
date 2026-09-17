import React, { useEffect, useState, useCallback } from 'react';
import { getApiUrl } from '../../lib/config';

interface AnalyticsData {
  poll_id: string;
  title: string;
  total_votes: number;
  options_breakdown: Record<string, number>;
  referrers_breakdown: Record<string, number>;
  votes_over_time: Record<string, number>;
}

interface Props {
  pollId: string;
  apiBaseUrl?: string;
}

export default function PollAnalytics({ pollId, apiBaseUrl }: Props) {
  const apiBase = apiBaseUrl || getApiUrl();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportingFormat, setExportingFormat] = useState<'csv' | 'json' | null>(null);

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = typeof window !== 'undefined' ? localStorage.getItem('polls-lab_auth_token') || 'dev-user-local' : 'dev-user-local';
      const res = await fetch(`${apiBase}/api/v1/analytics/${pollId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-dev-user-id': token,
        },
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Analytics request failed (${res.status})`);
      }

      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Failed to load telemetry metrics');
    } finally {
      setLoading(false);
    }
  }, [pollId, apiBase]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      setExportingFormat(format);
      const token = typeof window !== 'undefined' ? localStorage.getItem('polls-lab_auth_token') || 'dev-user-local' : 'dev-user-local';
      const res = await fetch(`${apiBase}/api/v1/analytics/${pollId}/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-dev-user-id': token,
        },
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Export failed with status ${res.status}`);
      }

      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `poll_${pollId}_analytics.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      alert(err.message || 'Failed to export analytics');
    } finally {
      setExportingFormat(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
        <span className="text-xs text-[#94a3b8] font-mono">Loading telemetry metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 rounded-2xl bg-[#111827] border border-red-900/40 text-center space-y-4 shadow-xl">
        <div className="w-10 h-10 rounded-full bg-red-950/60 border border-red-800/60 text-red-400 flex items-center justify-center mx-auto text-lg font-bold">
          !
        </div>
        <div className="space-y-1">
          <p className="text-sm font-semibold text-red-200">Unable to load analytics</p>
          <p className="text-xs text-[#94a3b8]">{error}</p>
        </div>
        <div className="flex justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={loadAnalytics}
            className="px-4 py-2 rounded-lg bg-[#1e293b] hover:bg-[#334155] text-white text-xs font-medium transition"
          >
            Retry Request
          </button>
          <a
            href="/dashboard"
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
          >
            Return to Dashboard
          </a>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 rounded-2xl bg-[#111827] border border-[#1e293b] text-center space-y-3">
        <p className="text-sm text-[#94a3b8]">No analytics recorded yet for this poll.</p>
        <a href="/dashboard" className="text-xs text-blue-400 hover:underline">
          Return to Dashboard
        </a>
      </div>
    );
  }

  const timelineEntries = Object.entries(data.votes_over_time);
  const maxTimelineVotes = Math.max(...Object.values(data.votes_over_time), 1);
  const optionsEntries = Object.entries(data.options_breakdown);
  const referrersEntries = Object.entries(data.referrers_breakdown);

  return (
    <div className="space-y-8">
      {/* Header Info & Export Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#1e293b]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
              Owner Analytics
            </span>
            <span className="text-xs font-mono text-[#64748b]">ID: {data.poll_id}</span>
          </div>
          <h2 className="text-2xl font-bold text-white">{data.title}</h2>
        </div>

        {/* Authenticated Download CSV & JSON buttons (PRD §4.3) */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={exportingFormat !== null}
            onClick={() => handleExport('csv')}
            className="btn-interactive inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#111827] hover:bg-[#1e293b] text-white text-xs font-medium border border-[#1e293b] hover:border-[#334155] transition shadow-xs disabled:opacity-50"
          >
            <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>{exportingFormat === 'csv' ? 'Exporting...' : 'Export CSV'}</span>
          </button>

          <button
            type="button"
            disabled={exportingFormat !== null}
            onClick={() => handleExport('json')}
            className="btn-interactive inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#111827] hover:bg-[#1e293b] text-white text-xs font-medium border border-[#1e293b] hover:border-[#334155] transition shadow-xs disabled:opacity-50"
          >
            <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>{exportingFormat === 'json' ? 'Exporting...' : 'Export JSON'}</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-[#111827] border border-[#1e293b]">
          <span className="text-xs text-[#94a3b8] font-medium">Total Valid Votes</span>
          <div className="text-3xl font-mono font-bold text-emerald-400 mt-1">
            {data.total_votes.toLocaleString()}
          </div>
          <span className="text-[11px] text-[#64748b]">Deduplicated via device token</span>
        </div>

        <div className="p-5 rounded-xl bg-[#111827] border border-[#1e293b]">
          <span className="text-xs text-[#94a3b8] font-medium">Recorded Referrer Sources</span>
          <div className="text-3xl font-mono font-bold text-blue-400 mt-1">
            {referrersEntries.length}
          </div>
          <span className="text-[11px] text-[#64748b]">Embedded sites & READMEs</span>
        </div>

        <div className="p-5 rounded-xl bg-[#111827] border border-[#1e293b]">
          <span className="text-xs text-[#94a3b8] font-medium">Active Engagement Days</span>
          <div className="text-3xl font-mono font-bold text-cyan-400 mt-1">
            {timelineEntries.length}
          </div>
          <span className="text-[11px] text-[#64748b]">Days with recorded votes</span>
        </div>
      </div>

      {/* Vote Timeline Histogram */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-[#1e293b] space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Votes Over Time (Velocity)</h3>
            <p className="text-xs text-[#94a3b8]">Daily voting volume distribution across active embeds.</p>
          </div>
          <span className="text-xs font-mono text-[#64748b]">Peak: {maxTimelineVotes} votes/day</span>
        </div>

        <div className="pt-4 flex items-end justify-between gap-2 h-44 border-b border-[#1e293b] pb-2">
          {timelineEntries.map(([date, count]) => {
            const heightPercent = Math.max(8, Math.round((count / maxTimelineVotes) * 100));
            return (
              <div key={date} className="flex-1 flex flex-col items-center gap-1 group">
                <span className="text-[10px] font-mono text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {count}
                </span>
                <div
                  style={{ height: `${heightPercent}%` }}
                  className="w-full max-w-[48px] bg-gradient-to-t from-blue-600 to-cyan-400 rounded-t-md transition-all duration-300 group-hover:brightness-125"
                ></div>
                <span className="text-[10px] font-mono text-[#64748b] truncate w-full text-center">
                  {date.slice(5)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Option Breakdown */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1e293b] space-y-4 shadow-xl">
          <h3 className="text-sm font-semibold text-white">Option Distribution</h3>
          <div className="space-y-4 pt-1">
            {optionsEntries.map(([optText, count]) => {
              const pct = data.total_votes > 0 ? ((count / data.total_votes) * 100).toFixed(1) : '0';
              return (
                <div key={optText} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-white truncate">{optText}</span>
                    <span className="text-emerald-400 font-mono">{count} votes ({pct}%)</span>
                  </div>
                  <div className="w-full bg-[#0b0f19] h-2 rounded-full overflow-hidden border border-[#1e293b]">
                    <div
                      className="bg-blue-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Referrers Breakdown Table */}
        <div className="p-6 rounded-2xl bg-[#111827] border border-[#1e293b] space-y-4 shadow-xl">
          <h3 className="text-sm font-semibold text-white">Embed & Referrer Sources</h3>
          <div className="divide-y divide-[#1e293b] text-xs">
            {referrersEntries.map(([ref, count]) => (
              <div key={ref} className="py-2.5 flex items-center justify-between gap-4">
                <span className="text-[#94a3b8] font-mono truncate max-w-[280px]">
                  {ref}
                </span>
                <span className="font-mono text-white font-semibold">
                  {count} votes
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
