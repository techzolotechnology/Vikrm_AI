import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: "admin" | "user";
  is_active: boolean;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  setSession: (params: { accessToken: string; refreshToken: string; user: AuthUser }) => void;
  setAccessToken: (accessToken: string) => void;
  clearSession: () => void;
  isAuthenticated: () => boolean;
}

/**
 * Tokens are persisted to localStorage so a page refresh doesn't force
 * a re-login — the access token alone is short-lived (30 min default)
 * and the refresh token is what actually matters for session length.
 * This is a standard SPA tradeoff; httpOnly-cookie refresh tokens are
 * a stronger alternative we can revisit if XSS surface becomes a concern.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: ({ accessToken, refreshToken, user }) =>
        set({ accessToken, refreshToken, user }),
      setAccessToken: (accessToken) => set({ accessToken }),
      clearSession: () => set({ accessToken: null, refreshToken: null, user: null }),
      isAuthenticated: () => get().accessToken !== null && get().user !== null,
    }),
    { name: "vikrm-auth" },
  ),
);
