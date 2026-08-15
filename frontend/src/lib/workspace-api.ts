import { apiClient } from "@/lib/api-client";

export const workspaceApi = {
  getModels: async (): Promise<{ providers: Record<string, string[]>; ollama_online: boolean; default_model?: string }> => {
    const res = await apiClient.get("/providers/models");
    return {
      providers: res.data.providers || { ollama: ["qwen3:8b"] },
      ollama_online: res.data.ollama_online ?? true,
      default_model: res.data.default_model || "qwen3:8b",
    };
  },

  searchHfModels: async (q: string) => {
    const res = await apiClient.get(`/huggingface/models?q=${encodeURIComponent(q)}`);
    return res.data.models;
  },

  searchHfDatasets: async (q: string) => {
    const res = await apiClient.get(`/huggingface/datasets?q=${encodeURIComponent(q)}`);
    return res.data.datasets;
  },
};

