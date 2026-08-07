export interface Attachment {
  id: number;
  conversation_id: number;
  message_id: number | null;
  filename: string;
  file_type: string;
  file_size: number;
  file_path: string;
  extracted_text?: string | null;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  role: "system" | "user" | "assistant";
  content: string;
  error: string | null;
  is_bookmarked?: boolean;
  edited_at?: string | null;
  created_at: string;
  attachments?: Attachment[];
}

export interface Conversation {
  id: number;
  title: string;
  provider: string;
  model: string;
  agent_id: number | null;
  is_pinned?: boolean;
  is_archived?: boolean;
  summary?: string | null;
  created_at: string;
  updated_at: string;
  attachments?: Attachment[];
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}
