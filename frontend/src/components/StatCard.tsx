import clsx from 'clsx';
import type { ReactNode } from 'react';

interface Props {
  icon: ReactNode;
  label: string;
  value: string | number;
  change?: string;
  color?: string;
  className?: string;
}

export default function StatCard({ icon, label, value, change, color = 'text-ds-blue', className }: Props) {
  return (
    <div className={clsx('glass rounded-xl p-5 hover:border-white/10 transition-all duration-200', className)}>
      <div className="flex items-start justify-between">
        <div className={clsx('p-2 rounded-lg', color.includes('blue') ? 'bg-ds-blue/10' : color.includes('green') ? 'bg-ds-green/10' : color.includes('amber') ? 'bg-ds-amber/10' : color.includes('red') ? 'bg-ds-red/10' : 'bg-ds-purple/10')}>
          {icon}
        </div>
        {change && <span className="text-xs text-ds-green font-medium">{change}</span>}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-ds-text-muted mt-1">{label}</p>
      </div>
    </div>
  );
}
