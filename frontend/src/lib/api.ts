import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";
import { tokenStore } from "./tokens";

const baseURL = (import.meta.env.VITE_API_BASE_URL ?? "") + "/api/v1";

export const api = axios.create({ baseURL, withCredentials: true });

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// --- Transparent refresh on 401 -------------------------------------------
let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${baseURL}/auth/refresh/`, { refresh });
    tokenStore.set(data.access, data.refresh);
    return data.access as string;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;
    const isAuthCall = original?.url?.includes("/auth/");

    if (status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshing = refreshing ?? refreshAccessToken();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` };
        return api(original);
      }
      // refresh failed — bubble up; the auth store will react and redirect.
      window.dispatchEvent(new Event("rd:logout"));
    }
    return Promise.reject(error);
  },
);

/** Normalize the backend's standardized error envelope into a string. */
export function apiErrorMessage(error: unknown, fallback = "Algo deu errado."): string {
  const err = error as AxiosError<{ error?: { message?: string; details?: Record<string, unknown> } }>;
  const env = err?.response?.data?.error;
  if (env?.details && Object.keys(env.details).length) {
    const first = Object.values(env.details)[0];
    if (Array.isArray(first)) return String(first[0]);
    if (typeof first === "string") return first;
  }
  return env?.message ?? err?.message ?? fallback;
}
