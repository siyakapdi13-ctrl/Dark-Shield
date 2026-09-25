import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import clsx from 'clsx';

interface BackButtonProps {
  fallback?: string;
  className?: string;
  label?: string;
}

/**
 * Intelligent back button:
 * - If there is prior navigation within the Dark Shield webapp (history index > 0),
 *   it navigates back one step in history (navigate(-1)).
 * - If this is the entry page of the application, calling navigate(-1) would exit the app
 *   to an external site (or about:blank). In this case, it safely navigates to fallback (default: '/').
 */
export default function BackButton({ fallback = '/', className, label }: BackButtonProps) {
  const navigate = useNavigate();

  const handleBack = () => {
    const historyIdx = window.history.state?.idx;

    if (typeof historyIdx === 'number' && historyIdx > 0) {
      navigate(-1);
    } else {
      navigate(fallback);
    }
  };

  return (
    <button
      type="button"
      onClick={handleBack}
      aria-label="Go back"
      className={clsx(
        'p-2 rounded-lg hover:bg-white/5 transition flex items-center gap-2 text-ds-text-muted hover:text-ds-text cursor-pointer',
        className
      )}
    >
      <ArrowLeft className="w-5 h-5" />
      {label && <span className="text-sm font-medium">{label}</span>}
    </button>
  );
}
