import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

// Inject Clerk token on every request
client.interceptors.request.use(async (config) => {
  try {
    // @ts-ignore — window.__clerk_token is set by ClerkProvider wrapper
    const token = window.__clerk_token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch { /* no-op */ }
  return config;
});

// Unwrap API envelope
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.error?.message || err.message || 'Network error';
    return Promise.reject(new Error(msg));
  }
);

export default client;
