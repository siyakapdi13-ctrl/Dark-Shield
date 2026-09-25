import { UserProfile } from '@clerk/clerk-react';
import { Settings } from 'lucide-react';

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || '';

function ClerkSettings() {
  return (
    <div className="glass rounded-xl p-6 flex justify-center">
      <UserProfile
        appearance={{
          elements: {
            rootBox: 'w-full max-w-2xl',
            card: 'bg-transparent shadow-none',
          },
        }}
      />
    </div>
  );
}

function DemoSettings() {
  return (
    <div className="glass rounded-xl p-8 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-ds-blue/10 flex items-center justify-center mx-auto">
        <Settings className="w-8 h-8 text-ds-blue" />
      </div>
      <h2 className="text-lg font-semibold">Demo Mode</h2>
      <p className="text-sm text-ds-text-muted max-w-md mx-auto">
        User settings and profile management are available when authentication is configured.
        Set <code className="px-1.5 py-0.5 bg-ds-surface-2 rounded text-ds-cyan text-xs">VITE_CLERK_PUBLISHABLE_KEY</code> in your <code className="px-1.5 py-0.5 bg-ds-surface-2 rounded text-ds-cyan text-xs">.env</code> file to enable.
      </p>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      {clerkKey ? <ClerkSettings /> : <DemoSettings />}
    </div>
  );
}
