import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in React component tree:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-ds-bg flex items-center justify-center p-6 text-ds-text">
          <div className="glass max-w-lg w-full p-8 rounded-2xl border border-ds-red/30 space-y-5 text-center">
            <div className="w-14 h-14 rounded-full bg-ds-red/10 text-ds-red flex items-center justify-center mx-auto">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Something went wrong</h2>
              <p className="text-xs text-ds-text-muted mt-1">
                An unexpected error occurred while rendering this page.
              </p>
            </div>
            {this.state.error?.message && (
              <div className="p-3 bg-black/40 rounded-lg text-left text-xs font-mono text-ds-red break-words overflow-auto max-h-32">
                {this.state.error.message}
              </div>
            )}
            <div className="flex gap-3 justify-center pt-2">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-ds-blue hover:bg-ds-blue-light text-white rounded-lg text-sm font-medium transition flex items-center gap-2 cursor-pointer"
              >
                <RefreshCw className="w-4 h-4" /> Reload Page
              </button>
              <a
                href="/"
                className="px-4 py-2 glass hover:bg-white/5 rounded-lg text-sm font-medium transition flex items-center gap-2"
              >
                <Home className="w-4 h-4" /> Go to Home
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
