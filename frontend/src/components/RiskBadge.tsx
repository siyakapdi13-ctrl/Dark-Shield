import clsx from 'clsx';
import { riskBg } from '../utils/formatters';

interface Props { level: string; className?: string }

export default function RiskBadge({ level, className }: Props) {
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full border', riskBg(level), className)}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {level === 'Low' ? 'Lower Risk' : level === 'Moderate' ? 'Moderate Risk' : 'High Risk'}
    </span>
  );
}
