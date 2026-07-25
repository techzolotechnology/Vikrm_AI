import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/store/use-auth-store";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 60_000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

// Concurrent 401s should trigger exactly one refresh call, with every
// other queued request waiting on the same in-flight promise rather
// than each firing its own refresh (which would race token rotation
// on the backend and log the user out).
let refreshPromise: Promise<string> | null = null;

async function performRefresh(): Promise<string> {
  const { refreshToken, user, setSession } = useAuthStore.getState();
  if (!refreshToken || !user) {
    throw new Error("No refresh token available");
  }

  const response = await axios.post(`${apiClient.defaults.baseURL}/auth/refresh`, {
    refresh_token: refreshToken,
  });
  const { access_token, refresh_token } = response.data as {
    access_token: string;
    refresh_token: string;
  };

  setSession({ accessToken: access_token, refreshToken: refresh_token, user });
  return access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableConfig | undefined;

    if (error.response?.status !== 401 || !originalRequest || originalRequest._retried) {
      return Promise.reject(error);
    }

    if (originalRequest.url?.includes("/auth/refresh")) {
      // The refresh call itself failed — session is unrecoverable.
      useAuthStore.getState().clearSession();
      return Promise.reject(error);
    }

    originalRequest._retried = true;

    try {
      if (!refreshPromise) {
        refreshPromise = performRefresh().finally(() => {
          refreshPromise = null;
        });
      }
      const newAccessToken = await refreshPromise;
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      useAuthStore.getState().clearSession();
      return Promise.reject(refreshError);
    }
  },
);
