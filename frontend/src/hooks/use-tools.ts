import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ToolExecution, ToolInfo } from "@/types/tool";

export function useToolsList() {
  return useQuery({
    queryKey: ["tools"],
    queryFn: async () => {
      const { data } = await apiClient.get<ToolInfo[]>("/tools");
      return data;
    },
  });
}

export function useExecuteTool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { toolName: string; input: string }) => {
      const { data } = await apiClient.post<ToolExecution>(
        `/tools/${params.toolName}/execute`,
        { input: params.input },
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tool-executions"] });
    },
  });
}

export function useToolExecutionHistory() {
  return useQuery({
    queryKey: ["tool-executions"],
    queryFn: async () => {
      const { data } = await apiClient.get<ToolExecution[]>("/tools/executions/history");
      return data;
    },
  });
}
