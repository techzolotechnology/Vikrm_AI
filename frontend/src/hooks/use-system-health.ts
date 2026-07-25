import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { HealthResponse, ReadinessResponse, VersionResponse } from "@/types/health";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await apiClient.get<HealthResponse>("/health");
      return data;
    },
    refetchInterval: 15_000,
  });
}

export function useReadiness() {
  return useQuery({
    queryKey: ["health", "ready"],
    queryFn: async () => {
      const { data } = await apiClient.get<ReadinessResponse>("/health/ready");
      return data;
    },
    refetchInterval: 15_000,
  });
}

export function useVersion() {
  return useQuery({
    queryKey: ["version"],
    queryFn: async () => {
      const { data } = await apiClient.get<VersionResponse>("/version");
      return data;
    },
  });
}
