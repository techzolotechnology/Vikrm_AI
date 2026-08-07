import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface SearchResultItem {
  id: number;
  category: "agent" | "chat" | "document" | "memory" | "workflow";
  title: string;
  description: string;
  path: string;
}

export function useGlobalSearch(query: string) {
  return useQuery({
    queryKey: ["global-search", query],
    queryFn: async () => {
      if (!query.trim()) return [];
      const { data } = await apiClient.get<{ results: SearchResultItem[] }>(
        `/search?q=${encodeURIComponent(query.trim())}`
      );
      return data.results;
    },
    enabled: query.trim().length > 0,
  });
}
