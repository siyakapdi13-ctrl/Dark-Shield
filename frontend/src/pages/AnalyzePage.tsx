import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeWebsite } from '../api/endpoints';
import WebsiteInput from '../components/WebsiteInput';
import AnalysisProgress from '../components/AnalysisProgress';
import { Shield } from 'lucide-react';
import { toast } from 'sonner';

export default function AnalyzePage() {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  const handleAnalyze = async (url: string) => {
    setLoading(true);
    setStep(0);
    // Simulate pipeline progress while real analysis runs
    const interval = setInterval(() => setStep(s => Math.min(s + 1, 8)), 600);
    try {
      const result = await analyzeWebsite(url);
      clearInterval(interval);
      setStep(9);
      toast.success('Analysis complete!');
      setTimeout(() => navigate(`/results/${result._id}`), 400);
    } catch (e: any) {
      clearInterval(interval);
      setLoading(false);
      setStep(0);
      toast.error(e.message || 'Analysis failed. Please try again.');
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-ds-blue/20 to-ds-cyan/20 mb-4">
          <Shield className="w-7 h-7 text-ds-blue" />
        </div>
        <h1 className="text-2xl font-bold">Analyze Website</h1>
        <p className="text-sm text-ds-text-muted mt-2">Enter a URL to scan for potentially deceptive UI/UX patterns.</p>
      </div>

      <WebsiteInput onSubmit={handleAnalyze} loading={loading} className="mb-6" />

      {loading && <AnalysisProgress currentStep={step} />}

      {!loading && (
        <div className="glass rounded-2xl p-6 text-center mt-8">
          <h3 className="text-sm font-semibold text-ds-text-muted mb-4">What we analyze</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-ds-text-muted">
            {['Page Content', 'DOM Structure', 'CSS/UI Signals', 'Pricing', 'Forms', 'Behavioral Signals', 'AI Semantics', 'Checkboxes'].map(c => (
              <div key={c} className="p-2.5 bg-ds-surface-2/50 rounded-lg">{c}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
