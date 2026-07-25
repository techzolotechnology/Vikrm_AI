import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { AgentTeam, TeamRun } from "@/types/agent-team";

export function useAgentTeams() {
  return useQuery({
    queryKey: ["agent-teams"],
    queryFn: async () => {
      const { data } = await apiClient.get<AgentTeam[]>("/agent-teams");
      return data;
    },
  });
}

export function useCreateAgentTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: {
      name: string;
      description?: string;
      manager_agent_id: number;
      member_agent_ids: number[];
    }) => {
      const { data } = await apiClient.post<AgentTeam>("/agent-teams", params);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-teams"] });
    },
  });
}

export function useDeleteAgentTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (teamId: number) => {
      await apiClient.delete(`/agent-teams/${teamId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-teams"] });
    },
  });
}

export function useRunAgentTeam(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (task: string) => {
      const { data } = await apiClient.post<TeamRun>(`/agent-teams/${teamId}/run`, { task });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-teams", teamId, "runs"] });
    },
  });
}

export function useAgentTeamRuns(teamId: number | null) {
  return useQuery({
    queryKey: ["agent-teams", teamId, "runs"],
    queryFn: async () => {
      const { data } = await apiClient.get<TeamRun[]>(`/agent-teams/${teamId}/runs`);
      return data;
    },
    enabled: teamId !== null,
  });
}
