import type { Detection } from '../types';
import { severityBg } from '../utils/formatters';
import { AlertTriangle, Info, ChevronDown, ChevronUp, ThumbsUp, ThumbsDown } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

interface Props {
  detection: Detection;
  onFeedback?: (type: string) => void;
}

export default function DetectionCard({ detection, onFeedback }: Props) {
  const [expanded, setExpanded] = useState(false);
  const d = detection;

  return (
    <div className="glass rounded-xl p-4 hover:border-white/10 transition-all duration-200 group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className={clsx('mt-0.5 p-1.5 rounded-lg', d.severity === 'High' ? 'bg-ds-red/10' : d.severity === 'Medium' ? 'bg-ds-amber/10' : 'bg-ds-cyan/10')}>
            <AlertTriangle className={clsx('w-4 h-4', d.severity === 'High' ? 'text-ds-red' : d.severity === 'Medium' ? 'text-ds-amber' : 'text-ds-cyan')} />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">{d.type}</h3>
            <p className="text-xs text-ds-text-muted mt-0.5">{d.location} · {d.sources.join(', ')}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={clsx('text-xs font-semibold px-2 py-0.5 rounded-full border', severityBg(d.severity))}>{d.severity}</span>
          <span className="text-xs font-mono text-ds-text-muted">{d.confidence}%</span>
        </div>
      </div>

      <div className="mt-3 pl-10">
        <p className="text-sm text-ds-text-muted italic">"{d.evidence}"</p>
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-xs text-ds-blue hover:text-ds-blue-light transition"
          aria-expanded={expanded}
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? 'Hide details' : 'Show explanation'}
        </button>

        {expanded && (
          <div className="mt-3 space-y-3 text-sm animate-in slide-in-from-top-2 duration-200">
            <div className="flex gap-2">
              <Info className="w-4 h-4 text-ds-blue mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-xs text-ds-text-muted mb-1">Why this may be deceptive</p>
                <p className="text-ds-text">{d.explanation}</p>
              </div>
            </div>
            <div className="bg-ds-blue/5 border border-ds-blue/10 rounded-lg p-3">
              <p className="font-medium text-xs text-ds-blue mb-1">Recommendation</p>
              <p className="text-sm">{d.recommendation}</p>
            </div>
            {onFeedback && (
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-ds-text-muted">Was this helpful?</span>
                <button onClick={() => onFeedback('correct')} className="p-1 rounded hover:bg-ds-green/10 text-ds-text-muted hover:text-ds-green transition" aria-label="Correct detection">
                  <ThumbsUp className="w-3.5 h-3.5" />
                </button>
                <button onClick={() => onFeedback('false_positive')} className="p-1 rounded hover:bg-ds-red/10 text-ds-text-muted hover:text-ds-red transition" aria-label="False positive">
                  <ThumbsDown className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
