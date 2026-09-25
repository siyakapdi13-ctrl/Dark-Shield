// All shared TypeScript types — single source of truth for frontend data shapes.

export interface Detection {
  id: string;
  pattern: string;
  type: string;
  severity: 'High' | 'Medium' | 'Low';
  confidence: number;
  confidenceLabel: string;
  evidence: string;
  evidenceItems: string[];
  location: string;
  element?: string;
  reason: string;
  explanation: string;
  recommendation: string;
  category: string;
  sources: string[];
}

export interface TrustScore {
  score: number;
  riskLevel: 'Low' | 'Moderate' | 'High';
  riskLabel: string;
  categories: Record<string, number>;
  weights: Record<string, number>;
  breakdown: { pattern: string; category: string; penalty: number; confidence: number; severity: string }[];
  confidence: number;
  disclaimer: string;
}

export interface Analysis {
  _id: string;
  userId: string;
  url: string;
  website: string;
  trustScore: number;
  riskLevel: 'Low' | 'Moderate' | 'High';
  patternsDetected: number;
  confidence: number;
  detections: Detection[];
  trust: TrustScore;
  features: Record<string, any>;
  summary: string;
  scraper: string;
  aiMode: string;
  createdAt: string;
}

export interface HistoryResponse {
  items: Analysis[];
  total: number;
  page: number;
  pageSize: number;
}

export interface Analytics {
  totalScans: number;
  totalPatterns: number;
  highRiskCount: number;
  avgTrustScore: number;
  recentScans: Analysis[];
  patternDistribution: Record<string, number>;
  riskDistribution: Record<string, number>;
  trustScoreTrend: { date: string; score: number; website: string }[];
  topPatterns: { name: string; count: number }[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
  sessionId: string;
  provider: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

export interface ApiError {
  success: false;
  error: { code: string; message: string };
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar: string;
}

export type RiskLevel = 'Low' | 'Moderate' | 'High';
export type Severity = 'High' | 'Medium' | 'Low';
