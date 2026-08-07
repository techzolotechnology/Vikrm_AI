import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface UserPreferences {
  theme?: string;
  accent_color?: string;
  reduce_animations?: boolean;
  compact_sidebar?: boolean;
  notifications?: {
    workflow_completion: boolean;
    agent_activity: boolean;
    system_health: boolean;
  };
}

export function useUserPreferences() {
  return useQuery({
    queryKey: ["user", "preferences"],
    queryFn: async () => {
      const { data } = await apiClient.get<UserPreferences>("/users/me/preferences");
      return data;
    },
  });
}

export function useUpdateUserPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<UserPreferences>) => {
      const { data } = await apiClient.patch<UserPreferences>("/users/me/preferences", payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user", "preferences"] });
    },
  });
}
