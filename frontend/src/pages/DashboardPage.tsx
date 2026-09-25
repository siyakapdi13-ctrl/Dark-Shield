import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Shield, AlertTriangle, BarChart3, TrendingDown } from 'lucide-react';
import { getAnalytics } from '../api/endpoints';
import type { Analytics } from '../types';
import StatCard from '../components/StatCard';
import RiskBadge from '../components/RiskBadge';
import { PageSkeleton } from '../components/LoadingSkeleton';
import { EmptyState, ErrorState } from '../components/EmptyState';
import { formatTime, riskColor } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const COLORS = ['#EF4444', '#F59E0B', '#22C55E', '#06B6D4', '#8B5CF6', '#2563EB'];

export default function DashboardPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    getAnalytics()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  if (loading) return <PageSkeleton />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <ErrorState message="Failed to load analytics." onRetry={load} />;

  const riskData = Object.entries(data.riskDistribution).map(([name, value]) => ({ name, value }));
  const patternData = data.topPatterns.slice(0, 6);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Welcome to Dark Shield</h1>
          <p className="text-sm text-ds-text-muted mt-1">Protect yourself from deceptive web experiences.</p>
        </div>
        <Link to="/analyze" className="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-ds-blue to-ds-cyan text-white font-medium text-sm rounded-xl hover:opacity-90 transition">
          <Search className="w-4 h-4" /> Analyze New Website
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="w-5 h-5 text-ds-blue" />} label="Websites Analyzed" value={data.totalScans} color="text-ds-blue" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-ds-red" />} label="Threats Detected" value={data.totalPatterns} color="text-ds-red" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-ds-green" />} label="Average Trust Score" value={data.avgTrustScore} color="text-ds-green" />
        <StatCard icon={<TrendingDown className="w-5 h-5 text-ds-amber" />} label="High-Risk Websites" value={data.highRiskCount} color="text-ds-amber" />
      </div>

      {data.totalScans === 0 ? (
        <EmptyState title="No scans yet" message="Analyze your first website to start seeing insights here." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Trust Score Trend */}
          {data.trustScoreTrend.length > 0 && (
            <div className="glass rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4">Trust Score Trend</h3>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data.trustScoreTrend}>
                  <XAxis dataKey="date" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                  <Line type="monotone" dataKey="score" stroke="#2563EB" strokeWidth={2} dot={{ r: 3, fill: '#2563EB' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Risk Distribution */}
          {riskData.length > 0 && (
            <div className="glass rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4">Risk Distribution</h3>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={50}>
                    {riskData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap justify-center gap-3 mt-2">
                {riskData.map((r, i) => (
                  <span key={r.name} className="flex items-center gap-1.5 text-xs text-ds-text-muted">
                    <span className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} /> {r.name}: {r.value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Most Common Patterns */}
          {patternData.length > 0 && (
            <div className="glass rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4">Most Common Dark Patterns</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={patternData} layout="vertical">
                  <XAxis type="number" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="count" fill="#2563EB" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Recent Scans */}
          {data.recentScans.length > 0 && (
            <div className="glass rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4">Recent Scans</h3>
              <div className="space-y-2">
                {data.recentScans.slice(0, 5).map((s: any) => (
                  <Link key={s._id} to={`/results/${s._id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{s.website}</p>
                      <p className="text-xs text-ds-text-muted">{formatTime(s.createdAt)}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-sm font-bold ${riskColor(s.riskLevel)}`}>{s.trustScore}</span>
                      <RiskBadge level={s.riskLevel} />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
