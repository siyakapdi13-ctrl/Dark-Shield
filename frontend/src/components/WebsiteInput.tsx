import { useState } from 'react';
import { Search, Loader2, Shield } from 'lucide-react';
import clsx from 'clsx';

interface Props {
  onSubmit: (url: string) => void;
  loading?: boolean;
  className?: string;
}

export default function WebsiteInput({ onSubmit, loading, className }: Props) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) { setError('Please enter a website URL.'); return; }
    if (trimmed.length < 4) { setError('URL is too short.'); return; }
    setError('');
    onSubmit(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className={clsx('w-full', className)}>
      <div className="relative">
        <div className="flex items-center gap-2 glass rounded-2xl p-2 focus-within:border-ds-blue/40 transition-all duration-300">
          <div className="pl-3">
            <Shield className="w-5 h-5 text-ds-blue" />
          </div>
          <input
            value={url}
            onChange={e => { setUrl(e.target.value); setError(''); }}
            placeholder="Enter website URL to analyze (e.g. https://example.com)"
            className="flex-1 bg-transparent py-3 px-2 text-sm placeholder:text-ds-text-muted/50 focus:outline-none"
            disabled={loading}
            aria-label="Website URL"
          />
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-ds-blue to-ds-cyan text-white font-medium text-sm rounded-xl hover:opacity-90 disabled:opacity-40 transition-all duration-200"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {loading ? 'Scanning...' : 'Scan Website'}
          </button>
        </div>
      </div>
      {error && <p className="text-xs text-ds-red mt-2 ml-4">{error}</p>}
    </form>
  );
}
