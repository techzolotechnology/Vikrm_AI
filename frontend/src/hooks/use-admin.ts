import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { AdminUser, SystemStats } from "@/types/admin";

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
