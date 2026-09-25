import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getHistory, deleteAnalysis } from '../api/endpoints';
import type { Analysis } from '../types';
import RiskBadge from '../components/RiskBadge';
import { PageSkeleton } from '../components/LoadingSkeleton';
import { EmptyState, ErrorState } from '../components/EmptyState';
import { Search, Trash2, Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { formatDate, riskColor } from '../utils/formatters';
import clsx from 'clsx';

export default function HistoryPage() {
  const [items, setItems] = useState<Analysis[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const pageSize = 10;

  const load = () => {
    setLoading(true);
    setError('');
    getHistory({ search, risk: riskFilter, page, pageSize })
      .then(res => { setItems(res.items); setTotal(res.total); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [page, riskFilter]);
  useEffect(() => { setPage(1); load(); }, [search, riskFilter]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this analysis?')) return;
    try {
      await deleteAnalysis(id);
      toast.success('Analysis deleted.');
      load();
    } catch { toast.error('Failed to delete.'); }
  };

  const totalPages = Math.ceil(total / pageSize);

  if (loading && items.length === 0) return <PageSkeleton />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Threat History</h1>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ds-text-muted" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search websites..."
            className="w-full bg-ds-surface-2 border border-ds-border rounded-lg pl-10 pr-4 py-2.5 text-sm placeholder:text-ds-text-muted/50 focus:outline-none focus:border-ds-blue transition"
          />
        </div>
        <div className="flex gap-1">
          {['', 'Low', 'Moderate', 'High'].map(r => (
            <button key={r} onClick={() => setRiskFilter(r)}
              className={clsx('px-3 py-2 text-xs rounded-lg transition', riskFilter === r ? 'bg-ds-blue text-white' : 'text-ds-text-muted glass hover:border-white/10')}>
              {r || 'All'}
            </button>
          ))}
        </div>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No history yet" message="Analyze websites to build your threat history." />
      ) : (
        <>
          {/* Table */}
          <div className="glass rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-ds-border text-xs text-ds-text-muted uppercase tracking-wider">
                    <th className="text-left px-4 py-3">Website</th>
                    <th className="text-center px-4 py-3">Trust Score</th>
                    <th className="text-center px-4 py-3">Patterns</th>
                    <th className="text-center px-4 py-3">Risk</th>
                    <th className="text-left px-4 py-3">Date</th>
                    <th className="text-center px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((a: any) => (
                    <tr key={a._id} className="border-b border-ds-border/50 hover:bg-white/[0.02] transition">
                      <td className="px-4 py-3">
                        <p className="font-medium truncate max-w-[200px]">{a.website}</p>
                        <p className="text-xs text-ds-text-muted truncate max-w-[200px]">{a.url}</p>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-bold ${riskColor(a.riskLevel)}`}>{a.trustScore}</span>
                      </td>
                      <td className="px-4 py-3 text-center">{a.patternsDetected}</td>
                      <td className="px-4 py-3 text-center"><RiskBadge level={a.riskLevel} /></td>
                      <td className="px-4 py-3 text-xs text-ds-text-muted">{formatDate(a.createdAt)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-1">
                          <Link to={`/results/${a._id}`} className="p-1.5 rounded-lg hover:bg-ds-blue/10 text-ds-text-muted hover:text-ds-blue transition" aria-label="View report">
                            <Eye className="w-4 h-4" />
                          </Link>
                          <button onClick={() => handleDelete(a._id)} className="p-1.5 rounded-lg hover:bg-ds-red/10 text-ds-text-muted hover:text-ds-red transition" aria-label="Delete">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-ds-text-muted">Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}</p>
              <div className="flex gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="p-2 glass rounded-lg disabled:opacity-30 hover:border-white/10 transition">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-2 glass rounded-lg disabled:opacity-30 hover:border-white/10 transition">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
