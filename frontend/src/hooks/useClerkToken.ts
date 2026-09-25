import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/clerk-react';

/**
 * Keeps window.__clerk_token in sync so the Axios interceptor always has a
 * fresh JWT. This hook should be rendered once near the app root.
 */
export function useClerkToken() {
  const { getToken, isSignedIn } = useAuth();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    const sync = async () => {
      if (isSignedIn) {
        try {
          const token = await getToken();
          (window as any).__clerk_token = token;
        } catch { /* no-op */ }
      } else {
        (window as any).__clerk_token = null;
      }
      if (mounted) setReady(true);
    };
    sync();
    const id = setInterval(sync, 50_000); // refresh before expiry
    return () => { mounted = false; clearInterval(id); };
  }, [getToken, isSignedIn]);

  return ready;
}
