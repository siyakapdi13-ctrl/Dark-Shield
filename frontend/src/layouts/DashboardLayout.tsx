import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  Shield, LayoutDashboard, Search, BarChart3, History, MessageCircle,
  Settings, Menu, X, ChevronRight, User
} from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analyze', icon: Search, label: 'Analyze' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/assistant', icon: MessageCircle, label: 'AI Assistant' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function DashboardLayout() {
  const { pathname } = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed lg:sticky top-0 left-0 z-50 h-screen w-64 bg-ds-surface border-r border-ds-border flex flex-col transition-transform duration-300',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        <div className="flex items-center gap-3 px-5 py-5 border-b border-ds-border">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-ds-blue to-ds-cyan flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wide">Dark Shield</h1>
            <p className="text-[10px] text-ds-text-muted tracking-widest uppercase">AI Protection</p>
          </div>
          <button className="ml-auto lg:hidden text-ds-text-muted" onClick={() => setSidebarOpen(false)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => {
            const active = pathname === to || pathname.startsWith(to + '/');
            return (
              <Link
                key={to}
                to={to}
                onClick={() => setSidebarOpen(false)}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  active
                    ? 'bg-ds-blue/10 text-ds-blue'
                    : 'text-ds-text-muted hover:text-ds-text hover:bg-white/5'
                )}
              >
                <Icon className="w-[18px] h-[18px]" />
                {label}
                {active && <ChevronRight className="w-4 h-4 ml-auto opacity-60" />}
              </Link>
            );
          })}
        </nav>

        <div className="px-4 py-4 border-t border-ds-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-ds-blue/10 flex items-center justify-center">
              <User className="w-4 h-4 text-ds-blue" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium truncate">Demo User</p>
              <p className="text-[10px] text-ds-text-muted truncate">demo@darkshield.app</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <header className="lg:hidden sticky top-0 z-30 glass px-4 py-3 flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)} className="text-ds-text-muted hover:text-ds-text" aria-label="Open menu">
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-ds-blue" />
            <span className="font-semibold text-sm">Dark Shield</span>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1400px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
