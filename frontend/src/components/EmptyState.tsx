import { AlertCircle, Inbox, WifiOff } from 'lucide-react';

interface EmptyProps { title?: string; message?: string; icon?: React.ReactNode }

export function EmptyState({ title = 'No data yet', message = 'Start analyzing websites to see results here.', icon }: EmptyProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-2xl bg-ds-surface-2/50 mb-4">
        {icon || <Inbox className="w-10 h-10 text-ds-text-muted" />}
      </div>
      <h3 className="text-lg font-semibold text-ds-text-muted">{title}</h3>
      <p className="text-sm text-ds-text-muted/70 mt-1 max-w-sm">{message}</p>
    </div>
  );
}

interface ErrorProps { message?: string; onRetry?: () => void }

export function ErrorState({ message = 'Something went wrong.', onRetry }: ErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-2xl bg-ds-red/10 mb-4">
        <AlertCircle className="w-10 h-10 text-ds-red" />
      </div>
      <h3 className="text-lg font-semibold">Error</h3>
      <p className="text-sm text-ds-text-muted mt-1 max-w-sm">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-4 px-4 py-2 bg-ds-blue text-white rounded-lg text-sm font-medium hover:bg-ds-blue-light transition">
          Try Again
        </button>
      )}
    </div>
  );
}

export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-2xl bg-ds-amber/10 mb-4">
        <WifiOff className="w-10 h-10 text-ds-amber" />
      </div>
      <h3 className="text-lg font-semibold">Connection Failed</h3>
      <p className="text-sm text-ds-text-muted mt-1 max-w-sm">Unable to connect to the Dark Shield API. Make sure the backend is running.</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-4 px-4 py-2 bg-ds-blue text-white rounded-lg text-sm font-medium hover:bg-ds-blue-light transition">
          Retry
        </button>
      )}
    </div>
  );
}
