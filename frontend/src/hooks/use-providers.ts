import { useQuery } from "@tanstack/react-query";
import { workspaceApi } from "@/lib/workspace-api";

export function useProviders() {
  const query = useQuery({
    queryKey: ["providers-models"],
    queryFn: () => workspaceApi.getModels(),
    staleTime: 30000,
    retry: 2,
  });

  const providerModels = query.data?.providers || { ollama: ["qwen3:8b"] };
  const ollamaOnline = query.data?.ollama_online ?? true;
  const defaultModel = query.data?.default_model || "qwen3:8b";
  const providerList = Object.keys(providerModels);

  return {
    providerModels,
    providerList,
    ollamaOnline,
    defaultModel,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
