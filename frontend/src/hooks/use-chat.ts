import { useCallback, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { streamSSE } from "@/lib/sse";
import type { Attachment, ChatMessage, Conversation, ConversationDetail } from "@/types/chat";

// ─── Conversations ───

export function useConversations(params?: {
  is_archived?: boolean;
  is_pinned?: boolean;
  search?: string;
}) {
  return useQuery({
    queryKey: ["conversations", params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.is_archived !== undefined) {
        queryParams.append("is_archived", String(params.is_archived));
      }
      if (params?.is_pinned !== undefined) {
        queryParams.append("is_pinned", String(params.is_pinned));
      }
      if (params?.search) {
        queryParams.append("search", params.search);
      }
      const { data } = await apiClient.get<Conversation[]>(`/conversations?${queryParams.toString()}`);
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

export function useUpdateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      title,
      is_pinned,
      is_archived,
    }: {
      id: number;
      title?: string;
      is_pinned?: boolean;
      is_archived?: boolean;
    }) => {
      const { data } = await apiClient.patch<Conversation>(`/conversations/${id}`, {
        title,
        is_pinned,
        is_archived,
      });
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.id] });
    },
  });
}

export function useDuplicateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: number) => {
      const { data } = await apiClient.post<Conversation>(`/conversations/${conversationId}/duplicate`);
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

// ─── Attachments ───

export function useUploadAttachment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ conversationId, file }: { conversationId: number; file: File }) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<Attachment>(
        `/conversations/${conversationId}/attachments`,
        formData
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.conversationId] });
    },
  });
}

export function useDeleteAttachment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (attachmentId: number) => {
      await apiClient.delete(`/attachments/${attachmentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

// ─── Message Actions ───

export function useBookmarkMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ conversationId, messageId }: { conversationId: number; messageId: number }) => {
      const { data } = await apiClient.post<ChatMessage>(
        `/conversations/${conversationId}/messages/${messageId}/bookmark`,
      );
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.conversationId] });
    },
  });
}

export function useDeleteMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ conversationId, messageId }: { conversationId: number; messageId: number }) => {
      await apiClient.delete(`/conversations/${conversationId}/messages/${messageId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["conversations", variables.conversationId] });
    },
  });
}

// ─── Export & Import ───

export function useExportConversation() {
  return useMutation({
    mutationFn: async (conversationId: number) => {
      const { data } = await apiClient.get(`/conversations/${conversationId}/export`);
      return data;
    },
  });
}

export function useImportConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (importData: Record<string, any>) => {
      const { data } = await apiClient.post<Conversation>("/conversations/import", importData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

// ─── Stream Hook ───

export function useChatStream(conversationId: number | null) {
  const queryClient = useQueryClient();
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextTempId = useRef(-1);
  const abortControllerRef = useRef<AbortController | null>(null);

  const seedMessages = useCallback((messages: ChatMessage[]) => {
    setLocalMessages(messages || []);
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, targetConversationId?: number, attachmentIds?: number[]) => {
      const targetId = targetConversationId ?? conversationId;
      if (targetId === null) return;
      setError(null);

      // Abort any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const userTempId = nextTempId.current--;
      const assistantTempId = nextTempId.current--;

      const userMessage: ChatMessage = {
        id: userTempId,
        role: "user",
        content,
        error: null,
        created_at: new Date().toISOString(),
      };
      const assistantMessage: ChatMessage = {
        id: assistantTempId,
        role: "assistant",
        content: "",
        error: null,
        created_at: new Date().toISOString(),
      };

      setLocalMessages((prev) => [...(prev || []), userMessage, assistantMessage]);
      setIsStreaming(true);

      let receivedAnyDelta = false;
      let streamError: string | null = null;
      try {
        for await (const event of streamSSE(
          `/conversations/${targetId}/messages/stream`,
          { content, attachment_ids: attachmentIds },
          controller.signal,
        )) {
          if (event.error) {
            streamError = event.error;
            setLocalMessages((prev) =>
              (prev || []).map((m) =>
                m.id === assistantTempId
                  ? { ...m, content: m.content || "", error: String(event.error) }
                  : m,
              ),
            );
          }
          if (event.delta !== undefined && event.delta !== null) {
            receivedAnyDelta = true;
            if (typeof event.delta === "object" || String(event.delta).trim() === "[object Object]") {
              console.error("BAD OBJECT DETECTED in useChatStream", {
                value: event.delta,
                typeof: typeof event.delta,
                constructor: (event.delta as any)?.constructor?.name,
                stack: new Error().stack,
              });
            }
            const deltaStr =
              typeof event.delta === "string"
                ? event.delta
                : typeof event.delta === "object"
                ? JSON.stringify(event.delta)
                : String(event.delta);
            setLocalMessages((prev) =>
              (prev || []).map((m) =>
                m.id === assistantTempId
                  ? { ...m, content: (m.content || "") + deltaStr }
                  : m,
              ),
            );
          }
          if (event.done) break;
        }
        if (receivedAnyDelta) {
          setError(null);
        } else if (streamError) {
          setError(String(streamError));
        }
      } catch (err: any) {
        if (err?.name === "AbortError") {
          console.info("[useChatStream] Stream stopped by user.");
          return;
        }
        const msg = typeof err === "string" ? err : (err?.message || "Something went wrong while streaming.");
        setError(String(msg));
        setLocalMessages((prev) =>
          (prev || []).map((m) =>
            m.id === assistantTempId
              ? { ...m, error: m.error || String(msg), content: m.content || "" }
              : m,
          ),
        );
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
        queryClient.invalidateQueries({ queryKey: ["conversations", targetId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      }
    },
    [conversationId, queryClient],
  );

  return { localMessages, isStreaming, error, sendMessage, seedMessages, stopStreaming };
}
