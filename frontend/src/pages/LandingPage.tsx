import { Link } from 'react-router-dom';
import {
  Shield, Search, BarChart3, Eye, MessageCircle, History, ArrowRight,
  AlertTriangle, Timer, CreditCard, CheckSquare, ChevronDown
} from 'lucide-react';

const FEATURES = [
  { icon: <Search className="w-5 h-5" />, title: 'AI-Powered Detection', desc: 'Hybrid rule + NLP + LLM engine detects 16+ dark pattern types with explainable confidence scores.' },
  { icon: <Eye className="w-5 h-5" />, title: 'Explainable Results', desc: 'Every detection answers: what was found, why it may be deceptive, and what to check.' },
  { icon: <BarChart3 className="w-5 h-5" />, title: 'Trust Score', desc: 'A 0-100 analytical score across transparency, pricing, UI fairness, checkout, and pressure.' },
  { icon: <Timer className="w-5 h-5" />, title: 'Real-Time Analysis', desc: 'Playwright renders JavaScript, BeautifulSoup parses HTML, and AI analyzes everything.' },
  { icon: <MessageCircle className="w-5 h-5" />, title: 'Consumer Assistant', desc: 'Ask Dark Shield AI about patterns, results, or checkout safety in plain language.' },
  { icon: <History className="w-5 h-5" />, title: 'Threat History', desc: 'Track every website you\'ve analyzed with searchable, filterable scan history.' },
];

const PATTERNS = [
  { icon: <AlertTriangle className="w-5 h-5 text-ds-red" />, name: 'Fake Scarcity', example: '"Only 2 left in stock!"', color: 'border-ds-red/20' },
  { icon: <CheckSquare className="w-5 h-5 text-ds-amber" />, name: 'Confirmshaming', example: '"No, I don\'t want to save money"', color: 'border-ds-amber/20' },
  { icon: <CreditCard className="w-5 h-5 text-ds-purple" />, name: 'Hidden Charges', example: 'Unexpected fees at checkout', color: 'border-ds-purple/20' },
  { icon: <CheckSquare className="w-5 h-5 text-ds-cyan" />, name: 'Pre-selected Add-ons', example: 'Automatically selected products', color: 'border-ds-cyan/20' },
];

export default function LandingPage() {
  // In demo mode, always show unauthenticated view (sign-in / get started links)
  // When Clerk is configured, this still works — unauthenticated users see sign-in links
  const isSignedIn = false;
  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-ds-blue to-ds-cyan flex items-center justify-center">
              <Shield className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">Dark Shield</span>
          </div>
          <div className="flex items-center gap-3">
            {isSignedIn ? (
              <Link to="/dashboard" className="px-4 py-2 bg-ds-blue text-white rounded-lg text-sm font-medium hover:bg-ds-blue-light transition">
                Dashboard
              </Link>
            ) : (
              <>
                <Link to="/sign-in" className="px-4 py-2 text-sm text-ds-text-muted hover:text-ds-text transition">Sign In</Link>
                <Link to="/sign-up" className="px-4 py-2 bg-ds-blue text-white rounded-lg text-sm font-medium hover:bg-ds-blue-light transition">
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(37,99,235,0.08)_0%,transparent_70%)]" />
        <div className="relative max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 glass rounded-full text-xs text-ds-cyan mb-6">
            <Shield className="w-3 h-3" /> AI-Powered Consumer Protection
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
            Detect Dark Patterns.
            <br />
            <span className="bg-gradient-to-r from-ds-blue to-ds-cyan bg-clip-text text-transparent">Shop With Confidence.</span>
          </h1>
          <p className="text-lg text-ds-text-muted max-w-2xl mx-auto mb-8">
            Dark Shield uses AI to analyze websites, identify potentially deceptive UI/UX patterns, and explain how those patterns may influence consumer decisions.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to={isSignedIn ? '/analyze' : '/sign-up'} className="px-6 py-3 bg-gradient-to-r from-ds-blue to-ds-cyan text-white font-semibold rounded-xl hover:opacity-90 transition flex items-center gap-2">
              <Search className="w-4 h-4" /> Analyze Website
            </Link>
            <Link to={isSignedIn ? '/dashboard' : '/sign-in'} className="px-6 py-3 glass rounded-xl font-medium text-sm hover:border-white/10 transition flex items-center gap-2">
              Explore Dashboard <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Visual flow */}
          <div className="mt-16 flex flex-wrap items-center justify-center gap-3 text-xs text-ds-text-muted">
            {['Website', 'AI Scanner', 'Pattern Detection', 'Trust Score'].map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <span className="px-3 py-1.5 glass rounded-lg">{step}</span>
                {i < 3 && <ChevronDown className="w-4 h-4 text-ds-blue rotate-[-90deg]" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-3">Powerful Protection Features</h2>
          <p className="text-sm text-ds-text-muted text-center mb-12 max-w-xl mx-auto">
            Detect. Explain. Understand. Decide.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(f => (
              <div key={f.title} className="glass rounded-xl p-6 hover:border-white/10 transition-all duration-200 group">
                <div className="p-2.5 rounded-lg bg-ds-blue/10 text-ds-blue w-fit mb-4 group-hover:scale-110 transition-transform">{f.icon}</div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-ds-text-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Dark Pattern Examples */}
      <section className="py-20 px-4 bg-ds-surface/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-3">Dark Patterns We Detect</h2>
          <p className="text-sm text-ds-text-muted text-center mb-12 max-w-xl mx-auto">
            Deceptive UI/UX techniques that manipulate consumer decisions.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {PATTERNS.map(p => (
              <div key={p.name} className={`glass rounded-xl p-5 border ${p.color} hover:border-white/10 transition`}>
                <div className="flex items-center gap-3 mb-3">
                  {p.icon}
                  <h3 className="font-semibold">{p.name}</h3>
                </div>
                <p className="text-sm text-ds-text-muted italic">"{p.example}"</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold mb-4">Ready to Shop Safer?</h2>
          <p className="text-ds-text-muted mb-8">Start analyzing websites for dark patterns in seconds.</p>
          <Link to={isSignedIn ? '/analyze' : '/sign-up'} className="px-8 py-3.5 bg-gradient-to-r from-ds-blue to-ds-cyan text-white font-semibold rounded-xl hover:opacity-90 transition inline-flex items-center gap-2">
            Get Started <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ds-border py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ds-text-muted">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-ds-blue" />
            <span>Dark Shield © {new Date().getFullYear()}</span>
          </div>
          <p>AI-Powered Dark Pattern Detection for Consumer Protection</p>
        </div>
      </footer>
    </div>
  );
}
