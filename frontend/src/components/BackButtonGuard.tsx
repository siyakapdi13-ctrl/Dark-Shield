import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * Intercepts the browser back button:
 * If the user would be thrown out of the application (e.g. from the first page in the tab session),
 * it redirects them safely to the home page '/' instead of exiting to an external website.
 */
export default function BackButtonGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if we are on the first entry of the session
    const isFirstEntry = !window.history.state?.inApp;
    if (isFirstEntry) {
      window.history.replaceState({ ...window.history.state, inApp: true, guard: true }, '');
    }

    const onPopState = (e: PopStateEvent) => {
      // If the popped state indicates we reached the entry point, or state is empty
      if (!e.state || e.state.guard) {
        if (location.pathname !== '/') {
          navigate('/', { replace: true });
        }
      }
    };

    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [navigate, location.pathname]);

  return <>{children}</>;
}
