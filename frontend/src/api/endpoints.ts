import client from './client';
import type { Analysis, Analytics, ApiResponse, ChatResponse, HistoryResponse } from '../types';

// ── Analysis ─────────────────────────────────────────────────────────────────
export const analyzeWebsite = (url: string) =>
  client.post<ApiResponse<Analysis>>('/api/analyze', { url }).then(r => r.data.data);

export const getResults = (id: string) =>
  client.get<ApiResponse<Analysis>>(`/api/results/${id}`).then(r => r.data.data);

// ── History ──────────────────────────────────────────────────────────────────
export const getHistory = (params: {
  search?: string; risk?: string; sort?: string; order?: number; page?: number; pageSize?: number;
}) =>
  client.get<ApiResponse<HistoryResponse>>('/api/history', { params }).then(r => r.data.data);

export const deleteAnalysis = (id: string) =>
  client.delete<ApiResponse<null>>(`/api/history/${id}`).then(r => r.data);

// ── Analytics ────────────────────────────────────────────────────────────────
export const getAnalytics = () =>
  client.get<ApiResponse<Analytics>>('/api/analytics').then(r => r.data.data);

// ── Trust Score ──────────────────────────────────────────────────────────────
export const getTrustScore = (id: string) =>
  client.get<ApiResponse<any>>(`/api/trust-score/${id}`).then(r => r.data.data);

// ── Chat ─────────────────────────────────────────────────────────────────────
export const sendChat = (message: string, sessionId?: string, analysisId?: string) =>
  client.post<ApiResponse<ChatResponse>>('/api/chat', {
    message, session_id: sessionId, analysis_id: analysisId,
  }).then(r => r.data.data);

// ── Feedback ─────────────────────────────────────────────────────────────────
export const submitFeedback = (data: {
  detection_id: string; analysis_id: string; pattern: string; feedback_type: string; comment?: string;
}) =>
  client.post<ApiResponse<any>>('/api/feedback', data).then(r => r.data);

// ── Auth ─────────────────────────────────────────────────────────────────────
export const getMe = () =>
  client.get<ApiResponse<any>>('/api/auth/me').then(r => r.data.data);

// ── Health ───────────────────────────────────────────────────────────────────
export const getHealth = () =>
  client.get<ApiResponse<any>>('/api/health').then(r => r.data.data);
