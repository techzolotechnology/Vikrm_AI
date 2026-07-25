import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ActivityItem, DashboardStats } from "@/types/analytics";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardStats>("/analytics/dashboard");
      return data;
    },
    refetchInterval: 30_000,
  });
}

export function useRecentActivity() {
  return useQuery({
    queryKey: ["analytics", "activity"],
    queryFn: async () => {
      const { data } = await apiClient.get<ActivityItem[]>("/analytics/activity");
      return data;
    },
    refetchInterval: 30_000,
  });
}
