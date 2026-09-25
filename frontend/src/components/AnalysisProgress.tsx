import { CheckCircle, Loader2, Circle } from 'lucide-react';
import clsx from 'clsx';

const STEPS = [
  'Fetching webpage',
  'Rendering JavaScript',
  'Parsing DOM structure',
  'Extracting CSS/UI signals',
  'Analyzing text content',
  'Analyzing pricing',
  'Detecting patterns',
  'Calculating Trust Score',
  'Generating explanation',
];

interface Props { currentStep: number; className?: string }

export default function AnalysisProgress({ currentStep, className }: Props) {
  return (
    <div className={clsx('glass rounded-2xl p-6', className)}>
      <h3 className="text-sm font-semibold mb-4 text-ds-text-muted uppercase tracking-wider">Analysis Pipeline</h3>
      <div className="space-y-3">
        {STEPS.map((step, i) => {
          const done = i < currentStep;
          const active = i === currentStep;
          return (
            <div key={step} className={clsx('flex items-center gap-3 text-sm transition-all duration-300', done ? 'text-ds-green' : active ? 'text-ds-blue' : 'text-ds-text-muted/40')}>
              {done ? (
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
              ) : active ? (
                <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 flex-shrink-0" />
              )}
              <span className={clsx(active && 'font-medium')}>{step}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
