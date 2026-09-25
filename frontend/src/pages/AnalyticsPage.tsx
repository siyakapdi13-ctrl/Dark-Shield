import { useEffect, useState } from 'react';
import { getAnalytics } from '../api/endpoints';
import type { Analytics } from '../types';
import StatCard from '../components/StatCard';
import { PageSkeleton } from '../components/LoadingSkeleton';
import { EmptyState, ErrorState } from '../components/EmptyState';
import { Shield, AlertTriangle, BarChart3, TrendingDown } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

const COLORS = ['#EF4444', '#F59E0B', '#22C55E', '#06B6D4', '#8B5CF6', '#2563EB', '#EC4899', '#10B981'];

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    getAnalytics().then(setData).catch(e => setError(e.message)).finally(() => setLoading(false));
  };
  useEffect(load, []);

  if (loading) return <PageSkeleton />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <ErrorState message="Failed to load analytics." onRetry={load} />;
  if (data.totalScans === 0) return <EmptyState title="No analytics yet" message="Analyze websites to build analytics data." />;

  const patternData = Object.entries(data.patternDistribution).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 8);
  const riskData = Object.entries(data.riskDistribution).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="w-5 h-5 text-ds-blue" />} label="Total Websites Scanned" value={data.totalScans} color="text-ds-blue" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-ds-red" />} label="Total Patterns Detected" value={data.totalPatterns} color="text-ds-red" />
        <StatCard icon={<TrendingDown className="w-5 h-5 text-ds-amber" />} label="High-Risk Websites" value={data.highRiskCount} color="text-ds-amber" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-ds-green" />} label="Average Trust Score" value={data.avgTrustScore} color="text-ds-green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {data.trustScoreTrend.length > 0 && (
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold mb-4">Trust Score Over Time</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={data.trustScoreTrend}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563EB" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="score" stroke="#2563EB" fill="url(#scoreGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {patternData.length > 0 && (
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold mb-4">Dark Pattern Categories</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={patternData} layout="vertical">
                <XAxis type="number" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" width={130} tick={{ fill: '#94A3B8', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {patternData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {riskData.length > 0 && (
          <div className="glass rounded-xl p-5 lg:col-span-2">
            <h3 className="text-sm font-semibold mb-4">Risk Distribution</h3>
            <div className="flex flex-col sm:flex-row items-center gap-8">
              <ResponsiveContainer width="100%" height={200} className="max-w-[250px]">
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={55}>
                    {riskData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-4">
                {riskData.map((r, i) => (
                  <div key={r.name} className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                    <span className="text-sm">{r.name}: <strong>{r.value}</strong></span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
