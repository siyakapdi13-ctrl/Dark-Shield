import { SignUp } from '@clerk/clerk-react';
import { Shield, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import BackButton from '../components/BackButton';

export default function SignUpPage() {
  return (
    <div className="flex flex-col items-center max-w-md mx-auto w-full">
      <div className="w-full flex items-center justify-between mb-6">
        <BackButton fallback="/" label="Home" />
        <Link
          to="/dashboard"
          className="text-xs text-ds-cyan hover:underline flex items-center gap-1 font-medium px-3 py-1.5 glass rounded-lg"
        >
          Skip to Demo <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="flex items-center gap-2.5 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-ds-blue to-ds-cyan flex items-center justify-center">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-xl">Dark Shield</span>
      </div>

      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" afterSignUpUrl="/dashboard" />
    </div>
  );
}
