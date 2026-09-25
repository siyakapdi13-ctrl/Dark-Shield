import clsx from 'clsx';

export function LoadingSkeleton({ className, lines = 3 }: { className?: string; lines?: number }) {
  return (
    <div className={clsx('space-y-3', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 bg-ds-surface-2 rounded animate-pulse" style={{ width: `${80 - i * 10}%` }} />
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="glass rounded-xl p-5 space-y-3 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-ds-surface-2 rounded-lg" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-ds-surface-2 rounded w-1/3" />
          <div className="h-3 bg-ds-surface-2 rounded w-1/2" />
        </div>
      </div>
      <div className="h-8 bg-ds-surface-2 rounded" />
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-ds-surface-2 rounded w-1/3" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
      </div>
      <div className="glass rounded-xl p-6 space-y-4">
        <div className="h-5 bg-ds-surface-2 rounded w-1/4" />
        <div className="h-48 bg-ds-surface-2 rounded" />
      </div>
    </div>
  );
}
