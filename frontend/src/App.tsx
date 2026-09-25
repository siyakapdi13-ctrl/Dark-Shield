import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { lazy, Suspense } from 'react';
import { Shield } from 'lucide-react';

// Layouts
import DashboardLayout from './layouts/DashboardLayout';
import AuthLayout from './layouts/AuthLayout';

// Components
import BackButtonGuard from './components/BackButtonGuard';

// Pages
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import AnalyzePage from './pages/AnalyzePage';
import ResultsPage from './pages/ResultsPage';
import InspectionPage from './pages/InspectionPage';
import TrustScorePage from './pages/TrustScorePage';
import AnalyticsPage from './pages/AnalyticsPage';
import HistoryPage from './pages/HistoryPage';
import AssistantPage from './pages/AssistantPage';
import SettingsPage from './pages/SettingsPage';
import SignInPage from './pages/SignInPage';
import SignUpPage from './pages/SignUpPage';

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route element={<AuthLayout />}>
        <Route path="/sign-in/*" element={<SignInPage />} />
        <Route path="/sign-up/*" element={<SignUpPage />} />
      </Route>

      {/* Dashboard & Tools */}
      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/results/:id" element={<ResultsPage />} />
        <Route path="/inspection/:id" element={<InspectionPage />} />
        <Route path="/trust-score/:id" element={<TrustScorePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function AppLoadingFallback() {
  return (
    <div className="min-h-screen bg-ds-bg flex flex-col items-center justify-center gap-4 text-ds-text">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-ds-blue to-ds-cyan flex items-center justify-center animate-pulse">
        <Shield className="w-6 h-6 text-white" />
      </div>
      <p className="text-xs text-ds-text-muted font-medium tracking-wide">Loading Dark Shield...</p>
    </div>
  );
}

/**
 * Lazy-loaded Clerk wrapper — only imported when VITE_CLERK_PUBLISHABLE_KEY is set.
 * This prevents @clerk/clerk-react from being bundled/loaded in demo mode.
 */
const ClerkApp = lazy(() => import('./ClerkApp'));

export default function App() {
  // If no Clerk key, render without Clerk (dev/demo mode)
  if (!clerkKey) {
    return (
      <BrowserRouter>
        <BackButtonGuard>
          <Toaster position="top-right" theme="dark" richColors />
          <AppRoutes />
        </BackButtonGuard>
      </BrowserRouter>
    );
  }

  // With Clerk — lazy-loaded to avoid importing @clerk/clerk-react in demo mode
  return (
    <Suspense fallback={<AppLoadingFallback />}>
      <ClerkApp>
        <AppRoutes />
      </ClerkApp>
    </Suspense>
  );
}
