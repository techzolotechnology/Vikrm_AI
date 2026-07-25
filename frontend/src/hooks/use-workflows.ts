import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { Workflow, WorkflowDefinition, WorkflowRun } from "@/types/workflow";

export function useWorkflows() {
  return useQuery({
    queryKey: ["workflows"],
    queryFn: async () => {
      const { data } = await apiClient.get<Workflow[]>("/workflows");
      return data;
    },
  });
}

export function useWorkflow(workflowId: number | null) {
  return useQuery({
    queryKey: ["workflows", workflowId],
    queryFn: async () => {
      const { data } = await apiClient.get<Workflow>(`/workflows/${workflowId}`);
      return data;
    },
    enabled: workflowId !== null,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { name: string; description?: string; definition: WorkflowDefinition }) => {
      const { data } = await apiClient.post<Workflow>("/workflows", params);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });
}

export function useUpdateWorkflow(workflowId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: {
      name?: string;
      description?: string;
      definition?: WorkflowDefinition;
    }) => {
      const { data } = await apiClient.patch<Workflow>(`/workflows/${workflowId}`, params);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows", workflowId] });
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (workflowId: number) => {
      await apiClient.delete(`/workflows/${workflowId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });
}

export function useRunWorkflow(workflowId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: string) => {
      const { data } = await apiClient.post<WorkflowRun>(`/workflows/${workflowId}/run`, { input });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows", workflowId, "runs"] });
    },
  });
}

export function useWorkflowRuns(workflowId: number | null) {
  return useQuery({
    queryKey: ["workflows", workflowId, "runs"],
    queryFn: async () => {
      const { data } = await apiClient.get<WorkflowRun[]>(`/workflows/${workflowId}/runs`);
      return data;
    },
    enabled: workflowId !== null,
  });
}

export function useTools() {
  return useQuery({
    queryKey: ["tools"],
    queryFn: async () => {
      const { data } = await apiClient.get<{ name: string; description: string }[]>("/tools");
      return data;
    },
  });
}
