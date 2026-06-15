import axios from 'axios';

function normalizeApiBase(raw: string | undefined): string {
  const value = (raw ?? '/api').trim();
  if (!value || value === '/') return '/api';

  const noTrailingSlash = value.replace(/\/+$/, '');
  if (noTrailingSlash.endsWith('/api')) return noTrailingSlash;
  if (/^https?:\/\//i.test(noTrailingSlash)) return `${noTrailingSlash}/api`;
  return noTrailingSlash.startsWith('/') ? noTrailingSlash : `/${noTrailingSlash}`;
}

export const http = axios.create({
  baseURL: normalizeApiBase(import.meta.env.VITE_API_BASE_URL),
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

http.interceptors.response.use(
  response => response,
  error => Promise.reject(error),
);

export default http;

