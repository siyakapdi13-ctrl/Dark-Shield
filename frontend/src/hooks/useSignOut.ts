import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

/**
 * Returns a sign-out handler that works in both Clerk and demo mode.
 *
 * - Clerk mode: dynamically imports `@clerk/clerk-react` and calls `signOut()`.
 * - Demo mode:  clears any local state and navigates to the landing page.
 */
export function useSignOut() {
  const navigate = useNavigate();

  const signOut = useCallback(async () => {
    if (clerkKey) {
      try {
        // Dynamic import so @clerk/clerk-react is never bundled in demo mode
        const { useClerk } = await import('@clerk/clerk-react');
        // useClerk is a hook and can't be called here — use the Clerk instance
        // exposed on the window instead (set by ClerkProvider).
        const clerk = (window as any).Clerk;
        if (clerk?.signOut) {
          await clerk.signOut();
          return; // Clerk redirects automatically
        }
      } catch {
        // Fall through to manual redirect
      }
    }

    // Demo mode / fallback
    (window as any).__clerk_token = null;
    navigate('/', { replace: true });
  }, [navigate]);

  return signOut;
}
