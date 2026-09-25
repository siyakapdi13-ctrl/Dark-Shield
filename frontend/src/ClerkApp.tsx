/**
 * ClerkApp — Lazy-loaded wrapper that provides Clerk authentication.
 * Only imported when VITE_CLERK_PUBLISHABLE_KEY is set.
 */
import { BrowserRouter } from 'react-router-dom';
import { ClerkProvider } from '@clerk/clerk-react';
import { Toaster } from 'sonner';
import { useClerkToken } from './hooks/useClerkToken';
import BackButtonGuard from './components/BackButtonGuard';

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

function TokenSync({ children }: { children: React.ReactNode }) {
  useClerkToken();
  return <>{children}</>;
}

export default function ClerkApp({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider publishableKey={clerkKey}>
      <BrowserRouter>
        <BackButtonGuard>
          <TokenSync>
            <Toaster position="top-right" theme="dark" richColors />
            {children}
          </TokenSync>
        </BackButtonGuard>
      </BrowserRouter>
    </ClerkProvider>
  );
}
