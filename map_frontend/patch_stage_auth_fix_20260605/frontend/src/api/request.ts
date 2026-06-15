import axios from 'axios';

/**
 * 规范化 API 根路径：后端路由挂载在 `/api` 下。
 * 若 .env 写成 `http://localhost:8000`（漏了 `/api`），会自动补为 `http://localhost:8000/api`。
 */
function normalizeApiBase(raw: string | undefined): string {
  const v = (raw ?? '/api').trim();
  if (!v || v === '/') return '/api';
  const noTrail = v.replace(/\/+$/, '');
  if (noTrail.endsWith('/api')) return noTrail;
  if (/^https?:\/\//i.test(noTrail)) {
    return `${noTrail}/api`;
  }
  return noTrail.startsWith('/') ? noTrail : `/${noTrail}`;
}

const resolvedBaseURL = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);

// Prefer a real login token. If absent, omit Authorization so the backend can use mapToken cookie auth.
function normalizeBearerToken(raw: string): string {
  const t = raw.trim();
  return /^Bearer\s+/i.test(t) ? t : `Bearer ${t}`;
}

function resolveAuthorizationHeader(): string | undefined {
  const envToken = import.meta.env.VITE_DEV_BEARER_TOKEN?.trim();
  if (typeof localStorage === 'undefined') {
    return envToken ? normalizeBearerToken(envToken) : undefined;
  }
  const raw = localStorage.getItem('map_access_token');
  if (raw?.trim()) {
    return normalizeBearerToken(raw);
  }
  return envToken ? normalizeBearerToken(envToken) : undefined;
}

export const http = axios.create({
  baseURL: resolvedBaseURL,
  timeout: 30_000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

http.interceptors.request.use((config) => {
  const authorization = resolveAuthorizationHeader();
  if (authorization) {
    config.headers.Authorization = authorization;
  } else {
    delete config.headers.Authorization;
  }
  const path = `${config.baseURL ?? ''}${config.url ?? ''}`;
  if (path.includes('portal-snapshot') || path.includes('committee')) {
    // eslint-disable-next-line no-console
    console.log(
      '%c🌐 [MAP Axios 即将请求]',
      'color:#A78BFA;font-weight:bold',
      String(config.method ?? 'GET').toUpperCase(),
      path,
      { params: config.params },
    );
  }
  return config;
});

http.interceptors.response.use(
  (res) => {
    const path = `${res.config.baseURL ?? ''}${res.config.url ?? ''}`;
    if (path.includes('portal-snapshot') || path.includes('committee')) {
      // eslint-disable-next-line no-console
      console.log(
        '%c🌐 [MAP Axios 响应]',
        'color:#34C759;font-weight:bold',
        res.status,
        path,
      );
    }
    return res;
  },
  (err) => {
    if (axios.isAxiosError(err) && err.config) {
      const path = `${err.config.baseURL ?? ''}${err.config.url ?? ''}`;
      if (path.includes('portal-snapshot') || path.includes('committee')) {
        // eslint-disable-next-line no-console
        console.error(
          '%c🌐 [MAP Axios 错误]',
          'color:#F97316;font-weight:bold',
          err.response?.status,
          path,
          err.message,
        );
      }
    }
    return Promise.reject(err);
  },
);

export default http;
