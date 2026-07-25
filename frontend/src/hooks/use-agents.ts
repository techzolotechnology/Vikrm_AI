import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { Agent, CreateAgentPayload } from "@/types/agent";

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const { data } = await apiClient.get<Agent[]>("/agents");
      return data;
    },
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateAgentPayload) => {
      const { data } = await apiClient.post<Agent>("/agents", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (agentId: number) => {
      await apiClient.delete(`/agents/${agentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });
}

export function useDuplicateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (agentId: number) => {
      const { data } = await apiClient.post<Agent>(`/agents/${agentId}/duplicate`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });
}

