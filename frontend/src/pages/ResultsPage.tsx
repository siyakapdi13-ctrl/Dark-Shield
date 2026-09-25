import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getResults, submitFeedback } from '../api/endpoints';
import type { Analysis } from '../types';
import TrustScore from '../components/TrustScore';
import RiskBadge from '../components/RiskBadge';
import DetectionCard from '../components/DetectionCard';
import { PageSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/EmptyState';
import { ExternalLink, Shield, AlertTriangle, Target, Activity, Eye } from 'lucide-react';
import BackButton from '../components/BackButton';
import { toast } from 'sonner';
import clsx from 'clsx';

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('All');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getResults(id)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleFeedback = async (detectionId: string, pattern: string, type: string) => {
    try {
      await submitFeedback({ detection_id: detectionId, analysis_id: id!, pattern, feedback_type: type });
      toast.success('Thank you for your feedback!');
    } catch { toast.error('Failed to submit feedback.'); }
  };

  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorState message={error || 'Analysis not found.'} />;

  const filtered = filter === 'All' ? data.detections : data.detections.filter(d => d.severity === filter);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <BackButton fallback="/dashboard" />
        <div className="min-w-0">
          <h1 className="text-xl font-bold truncate">{data.website}</h1>
          <a href={data.url} target="_blank" rel="noopener noreferrer" className="text-xs text-ds-blue flex items-center gap-1 hover:underline">
            {data.url} <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Score + Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass rounded-xl p-6 flex flex-col items-center justify-center relative">
          <TrustScore score={data.trustScore} />
          <RiskBadge level={data.riskLevel} className="mt-3" />
        </div>
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="glass rounded-xl p-5 flex flex-col items-center">
            <AlertTriangle className="w-6 h-6 text-ds-red mb-2" />
            <span className="text-2xl font-bold">{data.patternsDetected}</span>
            <span className="text-xs text-ds-text-muted">Dark Patterns</span>
          </div>
          <div className="glass rounded-xl p-5 flex flex-col items-center">
            <Target className="w-6 h-6 text-ds-amber mb-2" />
            <span className="text-2xl font-bold">{data.detections.length}</span>
            <span className="text-xs text-ds-text-muted">Suspicious Elements</span>
          </div>
          <div className="glass rounded-xl p-5 flex flex-col items-center">
            <Activity className="w-6 h-6 text-ds-green mb-2" />
            <span className="text-2xl font-bold">{data.confidence}%</span>
            <span className="text-xs text-ds-text-muted">Analysis Confidence</span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="glass rounded-xl p-5">
        <p className="text-sm leading-relaxed">{data.summary}</p>
      </div>

      {/* Trust Score Categories */}
      {data.trust?.categories && (
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4">Trust Score Breakdown</h3>
          <div className="space-y-3">
            {Object.entries(data.trust.categories).map(([cat, score]) => (
              <div key={cat} className="flex items-center gap-3">
                <span className="text-xs text-ds-text-muted w-40 flex-shrink-0">{cat}</span>
                <div className="flex-1 h-2 bg-ds-surface-2 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700" style={{
                    width: `${score}%`,
                    background: score >= 80 ? '#22C55E' : score >= 50 ? '#F59E0B' : '#EF4444',
                  }} />
                </div>
                <span className="text-xs font-mono w-8 text-right">{score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detections */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Detections ({filtered.length})</h3>
          <div className="flex gap-1">
            {['All', 'High', 'Medium', 'Low'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={clsx('px-3 py-1 text-xs rounded-lg transition', filter === f ? 'bg-ds-blue text-white' : 'text-ds-text-muted hover:bg-white/5')}>
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          {filtered.map(d => (
            <DetectionCard key={d.id} detection={d} onFeedback={(type) => handleFeedback(d.id, d.pattern, type)} />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <Link to={`/inspection/${id}`} className="inline-flex items-center gap-2 px-4 py-2 glass rounded-lg text-sm hover:border-white/10 transition">
          <Eye className="w-4 h-4" /> Page Inspection
        </Link>
        <Link to={`/trust-score/${id}`} className="inline-flex items-center gap-2 px-4 py-2 glass rounded-lg text-sm hover:border-white/10 transition">
          <Shield className="w-4 h-4" /> Detailed Trust Score
        </Link>
      </div>
    </div>
  );
}
