import { useState, useEffect, useCallback } from 'react';

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

export interface UserInfo {
  fullName: string;
  email: string;
  imageUrl?: string;
  isDemo: boolean;
}

const DEMO_USER: UserInfo = {
  fullName: 'Demo User',
  email: 'demo@darkshield.app',
  isDemo: true,
};

/**
 * Returns the current user's profile info.
 *
 * - Clerk mode: reads from the global Clerk instance (`window.Clerk.user`).
 * - Demo mode:  returns static placeholder data.
 */
export function useCurrentUser(): UserInfo {
  const [user, setUser] = useState<UserInfo>(DEMO_USER);

  const syncFromClerk = useCallback(() => {
    const clerk = (window as any).Clerk;
    const u = clerk?.user;
    if (u) {
      setUser({
        fullName: u.fullName || u.firstName || 'User',
        email: u.primaryEmailAddress?.emailAddress || '',
        imageUrl: u.imageUrl || undefined,
        isDemo: false,
      });
      return true; // resolved
    }
    return false;
  }, []);

  useEffect(() => {
    if (!clerkKey) return;

    // Try immediately — Clerk may already be loaded
    if (syncFromClerk()) return;

    // Otherwise poll briefly until the Clerk singleton is ready (max ~10 s)
    let attempts = 0;
    const id = setInterval(() => {
      if (syncFromClerk() || ++attempts >= 20) {
        clearInterval(id);
      }
    }, 500);

    return () => clearInterval(id);
  }, [syncFromClerk]);

  return user;
}
