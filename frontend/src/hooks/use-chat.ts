import { useCallback, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { streamSSE } from "@/lib/sse";
import type { ChatMessage, Conversation, ConversationDetail } from "@/types/chat";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: async () => {
      const { data } = await apiClient.get<Conversation[]>("/conversations");
      return data;
    },
  });
}

export function useConversation(conversationId: number | null) {
  return useQuery({
    queryKey: ["conversations", conversationId],
    queryFn: async () => {
      const { data } = await apiClient.get<ConversationDetail>(
        `/conversations/${conversationId}`,
      );
      return data;
    },
    enabled: conversationId !== null,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (
      params: { title?: string; provider?: string; model?: string; agent_id?: number } = {},
    ) => {
      const { data } = await apiClient.post<Conversation>("/conversations", params);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: number) => {
      await apiClient.delete(`/conversations/${conversationId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

/**
 * Manages the live-streaming portion of a conversation. Confirmed
 * history comes from `useConversation` (React Query); this hook layers
 * an in-flight user message + incrementally-growing assistant message
 * on top while a stream is active, then invalidates the conversation
 * query once the stream completes to reconcile with persisted state.
 */
export function useChatStream(conversationId: number | null) {
  const queryClient = useQueryClient();
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextTempId = useRef(-1);

  const seedMessages = useCallback((messages: ChatMessage[]) => {
    setLocalMessages(messages);
  }, []);

  const sendMessage = useCallback(
    async (content: string, targetConversationId?: number) => {
      const targetId = targetConversationId ?? conversationId;
      if (targetId === null) return;
      setError(null);

      const userMessage: ChatMessage = {
        id: nextTempId.current--,
        role: "user",
        content,
        error: null,
        created_at: new Date().toISOString(),
      };
      const assistantMessage: ChatMessage = {
        id: nextTempId.current--,
        role: "assistant",
        content: "",
        error: null,
        created_at: new Date().toISOString(),
      };

      setLocalMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      try {
        for await (const event of streamSSE(
          `/conversations/${targetId}/messages/stream`,
          { content },
        )) {
          if (event.error) {
            setError(event.error);
          }
          if (event.delta) {
            setLocalMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessage.id ? { ...m, content: m.content + event.delta } : m,
              ),
            );
          }
          if (event.done) break;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong while streaming.");
      } finally {
        setIsStreaming(false);
        queryClient.invalidateQueries({ queryKey: ["conversations", targetId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      }
    },
    [conversationId, queryClient],
  );

  return { localMessages, isStreaming, error, sendMessage, seedMessages };
}
