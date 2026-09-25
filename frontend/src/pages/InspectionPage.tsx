import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getResults } from '../api/endpoints';
import type { Analysis } from '../types';
import DetectionCard from '../components/DetectionCard';
import { PageSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/EmptyState';
import { Globe, Shield } from 'lucide-react';
import BackButton from '../components/BackButton';
import clsx from 'clsx';

export default function InspectionPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<number>(0);

  useEffect(() => {
    if (!id) return;
    getResults(id).then(setData).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <PageSkeleton />;
  if (error || !data) return <ErrorState message={error || 'Not found.'} />;

  const detection = data.detections[selected];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <BackButton fallback={`/results/${id}`} />
        <h1 className="text-xl font-bold">Page Inspection — {data.website}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-[600px]">
        {/* Webpage Preview */}
        <div className="glass rounded-xl overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-ds-border">
            <Globe className="w-4 h-4 text-ds-text-muted" />
            <span className="text-xs text-ds-text-muted truncate">{data.url}</span>
          </div>
          <div className="flex-1 p-4 overflow-auto">
            <div className="bg-white/5 rounded-lg p-6 min-h-[400px]">
              <p className="text-sm text-ds-text-muted mb-4">Suspicious elements highlighted:</p>
              {data.detections.map((d, i) => (
                <button
                  key={d.id}
                  onClick={() => setSelected(i)}
                  className={clsx(
                    'block w-full text-left p-3 mb-2 rounded-lg border transition-all',
                    selected === i ? 'border-ds-blue bg-ds-blue/10' : 'border-ds-border/50 hover:border-ds-blue/30'
                  )}
                >
                  <p className="text-xs font-semibold">{d.type}</p>
                  <p className="text-xs text-ds-text-muted italic mt-1 truncate">"{d.evidence}"</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* AI Analysis Panel */}
        <div className="glass rounded-xl overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-ds-border">
            <Shield className="w-4 h-4 text-ds-blue" />
            <span className="text-sm font-semibold">AI Analysis</span>
          </div>
          <div className="flex-1 p-4 overflow-auto">
            {detection ? (
              <div className="space-y-4">
                <DetectionCard detection={detection} />
                {detection.evidenceItems.length > 1 && (
                  <div className="glass rounded-lg p-4">
                    <h4 className="text-xs font-semibold text-ds-text-muted mb-2">Additional Evidence</h4>
                    {detection.evidenceItems.slice(1).map((e, i) => (
                      <p key={i} className="text-xs text-ds-text-muted italic mb-1">• "{e}"</p>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-ds-text-muted">Select an element to see the analysis.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
