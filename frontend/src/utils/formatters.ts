import type { RiskLevel, Severity } from '../types';

export const riskColor = (level: RiskLevel | string): string => {
  switch (level) {
    case 'Low': return 'text-ds-green';
    case 'Moderate': return 'text-ds-amber';
    case 'High': return 'text-ds-red';
    default: return 'text-ds-text-muted';
  }
};

export const riskBg = (level: RiskLevel | string): string => {
  switch (level) {
    case 'Low': return 'bg-ds-green/10 text-ds-green border-ds-green/20';
    case 'Moderate': return 'bg-ds-amber/10 text-ds-amber border-ds-amber/20';
    case 'High': return 'bg-ds-red/10 text-ds-red border-ds-red/20';
    default: return 'bg-ds-surface-2 text-ds-text-muted border-ds-border';
  }
};

export const severityColor = (s: Severity | string): string => {
  switch (s) {
    case 'High': return 'text-ds-red';
    case 'Medium': return 'text-ds-amber';
    case 'Low': return 'text-ds-cyan';
    default: return 'text-ds-text-muted';
  }
};

export const severityBg = (s: Severity | string): string => {
  switch (s) {
    case 'High': return 'bg-ds-red/10 text-ds-red border-ds-red/20';
    case 'Medium': return 'bg-ds-amber/10 text-ds-amber border-ds-amber/20';
    case 'Low': return 'bg-ds-cyan/10 text-ds-cyan border-ds-cyan/20';
    default: return 'bg-ds-surface-2 text-ds-text-muted border-ds-border';
  }
};

export const formatDate = (date: string | Date): string => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export const formatTime = (date: string | Date): string => {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

export const truncate = (s: string, len = 50): string =>
  s.length > len ? s.slice(0, len) + '…' : s;

export const scoreLabel = (score: number): string => {
  if (score >= 80) return 'Lower Risk';
  if (score >= 50) return 'Moderate Risk';
  return 'High Risk';
};
