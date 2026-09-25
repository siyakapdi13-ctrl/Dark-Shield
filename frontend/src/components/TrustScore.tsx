import clsx from 'clsx';

interface Props {
  score: number;
  size?: number;
  label?: string;
  className?: string;
}

export default function TrustScore({ score, size = 160, label, className }: Props) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? '#22C55E' : score >= 50 ? '#F59E0B' : '#EF4444';

  return (
    <div className={clsx('flex flex-col items-center', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#1E293B" strokeWidth="8" />
        <circle
          cx={size/2} cy={size/2} r={radius} fill="none"
          stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="trust-ring"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-3xl font-bold" style={{ color }}>{score}</span>
        <span className="text-xs text-ds-text-muted">/100</span>
      </div>
      {label && <p className="mt-2 text-sm font-medium text-ds-text-muted">{label}</p>}
    </div>
  );
}
