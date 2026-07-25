import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { type AuthUser, useAuthStore } from "@/store/use-auth-store";

// ─── Types ─────────────────────────────────────────────────────────────────────

interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface EmailLoginRequest {
  email: string;
  password: string;
}

interface EmailRegisterRequest {
  full_name: string;
  email: string;
  password: string;
}

interface ForgotPasswordRequest {
  email: string;
}

interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

// ─── API functions ─────────────────────────────────────────────────────────────

async function exchangeGoogleIdToken(idToken: string): Promise<TokenPairResponse> {
  const { data } = await apiClient.post<TokenPairResponse>("/auth/google", {
    id_token: idToken,
  });
  return data;
}

async function loginWithEmail(body: EmailLoginRequest): Promise<TokenPairResponse> {
  const { data } = await apiClient.post<TokenPairResponse>("/auth/login", body);
  return data;
}

async function registerWithEmail(body: EmailRegisterRequest): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>("/auth/register", body);
  return data;
}

async function requestPasswordReset(body: ForgotPasswordRequest): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>("/auth/forgot-password", body);
  return data;
}

async function resetPassword(body: ResetPasswordRequest): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>("/auth/reset-password", body);
  return data;
}

async function verifyEmail(token: string): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>("/auth/verify-email", { token });
  return data;
}

async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await apiClient.get<AuthUser>("/auth/me");
  return data;
}

// ─── Helper: set session after login ──────────────────────────────────────────

async function hydrateSession(tokens: TokenPairResponse): Promise<AuthUser> {
  useAuthStore.getState().setAccessToken(tokens.access_token);
  const user = await fetchCurrentUser();
  useAuthStore.getState().setSession({
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    user,
  });
  return user;
}

// ─── Hooks ─────────────────────────────────────────────────────────────────────

export function useGoogleSignIn() {
  return useMutation({
    mutationFn: async (googleIdToken: string) => {
      console.log("[Auth] Credential sent to backend (/api/v1/auth/google)");
      const tokens = await exchangeGoogleIdToken(googleIdToken);
      console.log("[Auth] JWT tokens received from backend. Hydrating auth session...");
      const user = await hydrateSession(tokens);
      console.log("[Auth] Session created successfully. User:", user.email, "ID:", user.id);
      return user;
    },
    onError: (err) => {
      console.error("[Auth Error] Google sign-in mutation failed:", err);
    },
  });
}


export function useEmailSignIn() {
  return useMutation({
    mutationFn: async (body: EmailLoginRequest) => {
      const tokens = await loginWithEmail(body);
      return hydrateSession(tokens);
    },
  });
}

export function useEmailRegister() {
  return useMutation({
    mutationFn: registerWithEmail,
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: requestPasswordReset,
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: resetPassword,
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: verifyEmail,
  });
}

export function useCurrentUser() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: fetchCurrentUser,
    enabled: isAuthenticated,
    retry: false,
  });
}

export function useLogout() {
  const { refreshToken, clearSession } = useAuthStore();

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await apiClient.post("/auth/logout", { refresh_token: refreshToken });
      }
    },
    onSettled: () => {
      clearSession();
    },
  });
}
