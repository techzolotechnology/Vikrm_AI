import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { AdminUser, SystemStats } from "@/types/admin";

export interface SystemLog {
  timestamp: string;
  level: string;
  message: string;
  source: string;
}

export interface ModelConfig {
  provider: string;
  model: string;
  status: string;
  latency_ms: number;
}

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin", "users"],
    queryFn: async () => {
      const { data } = await apiClient.get<AdminUser[]>("/admin/users");
      return data;
    },
  });
}

export function useSystemStats() {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: async () => {
      const { data } = await apiClient.get<SystemStats>("/admin/stats");
      return data;
    },
  });
}

export function useSystemLogs() {
  return useQuery({
    queryKey: ["admin", "logs"],
    queryFn: async () => {
      const { data } = await apiClient.get<SystemLog[]>("/admin/logs");
      return data;
    },
  });
}

export function useModelConfigs() {
  return useQuery({
    queryKey: ["admin", "models"],
    queryFn: async () => {
      const { data } = await apiClient.get<ModelConfig[]>("/admin/models");
      return data;
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { userId: number; role?: string; is_active?: boolean }) => {
      const { data } = await apiClient.patch<AdminUser>(`/admin/users/${params.userId}`, {
        role: params.role,
        is_active: params.is_active,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "stats"] });
    },
  });
}
