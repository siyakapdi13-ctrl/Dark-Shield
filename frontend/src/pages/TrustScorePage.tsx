import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getTrustScore } from '../api/endpoints';
import TrustScore from '../components/TrustScore';
import RiskBadge from '../components/RiskBadge';
import { PageSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/EmptyState';
import { Info } from 'lucide-react';
import BackButton from '../components/BackButton';

export default function TrustScorePage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    getTrustScore(id).then(setData).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorState message={error || 'Not found.'} />;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <BackButton fallback={`/results/${id}`} />
        <div>
          <h1 className="text-xl font-bold">Trust Score — {data.website}</h1>
          <p className="text-xs text-ds-text-muted">{data.url}</p>
        </div>
      </div>

      <div className="glass rounded-xl p-8 flex flex-col items-center">
        <TrustScore score={data.score} size={200} />
        <RiskBadge level={data.riskLevel} className="mt-4" />
        <p className="text-sm text-center text-ds-text-muted mt-3 max-w-md">{data.riskLabel}</p>
      </div>

      <div className="glass rounded-xl p-5">
        <h3 className="text-sm font-semibold mb-4">Category Breakdown</h3>
        <div className="space-y-4">
          {data.categories && Object.entries(data.categories).map(([cat, score]: [string, any]) => (
            <div key={cat}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm">{cat}</span>
                <span className="text-sm font-mono font-bold" style={{ color: score >= 80 ? '#22C55E' : score >= 50 ? '#F59E0B' : '#EF4444' }}>
                  {score}/100
                </span>
              </div>
              <div className="h-2.5 bg-ds-surface-2 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-1000" style={{
                  width: `${score}%`,
                  background: score >= 80 ? '#22C55E' : score >= 50 ? '#F59E0B' : '#EF4444',
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {data.breakdown?.length > 0 && (
        <div className="glass rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-4">Penalty Breakdown</h3>
          <div className="space-y-2">
            {data.breakdown.map((b: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-ds-border/30 last:border-0">
                <div>
                  <span className="text-sm">{b.pattern}</span>
                  <span className="text-xs text-ds-text-muted ml-2">({b.category})</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-ds-text-muted">{b.confidence}%</span>
                  <span className="text-xs font-mono text-ds-red">-{b.penalty}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-start gap-2 p-4 glass rounded-xl">
        <Info className="w-4 h-4 text-ds-blue mt-0.5 flex-shrink-0" />
        <p className="text-xs text-ds-text-muted">{data.disclaimer}</p>
      </div>
    </div>
  );
}
