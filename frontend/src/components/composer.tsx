import { useEffect, useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Mic,
  Paperclip,
  X,
  FileText,
  Smile,
  AlertCircle,
  Loader2,
  Square,
} from "lucide-react";

import { useUploadAttachment } from "@/hooks/use-chat";
import type { Attachment } from "@/types/chat";

interface ComposerProps {
  onSend: (content: string, attachmentIds?: number[]) => void;
  disabled: boolean;
  conversationId: number | null;
  onEnsureConversation?: () => Promise<number>;
  onStop?: () => void;
}

const EMOJIS = ["👍", "❤️", "🔥", "🚀", "💡", "🧠", "✨", "🎉", "⚡", "🤖", "📝", "📊"];

function parseErrorMessage(err: any, defaultMsg: string): string {
  if (!err) return defaultMsg;
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const item = detail[0];
    if (typeof item === "string") return item;
    if (typeof item === "object" && item !== null) {
      return item.msg || item.message || defaultMsg;
    }
  }
  if (typeof detail === "object" && detail !== null) {
    return detail.msg || detail.message || defaultMsg;
  }
  if (typeof err?.message === "string") return err.message;
  return defaultMsg;
}

export function Composer({ onSend, disabled, conversationId, onEnsureConversation, onStop }: ComposerProps) {
  const [value, setValue] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);

  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([]);
  const uploadAttachment = useUploadAttachment();

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: any) => {
        let currentTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setValue((prev) => {
          const trimmedPrev = prev.trim();
          return trimmedPrev ? `${trimmedPrev} ${currentTranscript}` : currentTranscript;
        });
      };

      recognition.onerror = (event: any) => {
        setSpeechError("Speech recognition error: " + (event.error || "Denied"));
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      setSpeechError("Web Speech API is not supported in this browser.");
      return;
    }
    setSpeechError(null);
    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) {
        setSpeechError("Could not access microphone.");
        setIsRecording(false);
      }
    }
  };

  const handleFileUpload = async (files: FileList | File[]) => {
    let targetConvId = conversationId;
    if (!targetConvId && onEnsureConversation) {
      try {
        targetConvId = await onEnsureConversation();
      } catch (err) {
        setSpeechError("Failed to initialize conversation for attachment.");
        return;
      }
    }

    if (!targetConvId) {
      setSpeechError("Please select or start a conversation first.");
      return;
    }

    const fileList = Array.from(files);
    for (const file of fileList) {
      setUploadingFiles((prev) => [...prev, file.name]);
      try {
        const att = await uploadAttachment.mutateAsync({ conversationId: targetConvId, file });
        if (att && att.id) {
          setAttachments((prev) => [...prev, att]);
        }
      } catch (err: any) {
        const errorMessage = parseErrorMessage(err, `Failed to upload ${file.name}`);
        setSpeechError(errorMessage);
      } finally {
        setUploadingFiles((prev) => prev.filter((name) => name !== file.name));
      }
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      handleFileUpload(e.clipboardData.files);
    }
  };

  const removeAttachment = (id: number) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  };

  const submit = () => {
    const trimmed = value.trim();
    if ((!trimmed && attachments.length === 0) || disabled) return;
    const attachmentIds = attachments.map((a) => a.id);
    onSend(trimmed || "Sent attached documents.", attachmentIds);
    setValue("");
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  };

  const charCount = value.length;
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;

  return (
    <div
      className="relative flex flex-col gap-2.5"
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
        accept="image/*,.pdf,.docx,.doc,.txt,.csv,.xlsx,.md,.json,.py,.js,.ts,.tsx"
      />

      {/* Drag & Drop Overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl border-2 border-dashed border-primary bg-background/90 backdrop-blur-md"
          >
            <div className="flex flex-col items-center gap-2 text-primary">
              <Paperclip className="h-8 w-8 animate-bounce" />
              <span className="font-display text-sm font-semibold">Drop files here to attach</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error banner */}
      {speechError && (
        <div className="flex items-center gap-2 rounded-xl border border-warning/30 bg-warning/10 px-3.5 py-2 text-xs text-warning">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1">{String(speechError)}</span>
          <button onClick={() => setSpeechError(null)} className="hover:text-white">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Attachment Preview Chips */}
      {(attachments.length > 0 || uploadingFiles.length > 0) && (
        <div className="flex flex-wrap items-center gap-2 px-1">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center gap-2 rounded-xl border border-border/80 bg-surface/70 px-3 py-1.5 text-xs text-white/90 backdrop-blur-sm"
            >
              <FileText className="h-3.5 w-3.5 text-accent" />
              <span className="max-w-[140px] truncate font-medium">{att.filename}</span>
              <span className="font-mono text-[10px] text-white/40">
                {(att.file_size / 1024).toFixed(0)}KB
              </span>
              <button
                onClick={() => removeAttachment(att.id)}
                className="text-white/40 hover:text-danger transition-colors ml-1"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}

          {uploadingFiles.map((filename) => (
            <div
              key={filename}
              className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs text-primary"
            >
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span className="max-w-[140px] truncate font-medium">Uploading {filename}...</span>
            </div>
          ))}
        </div>
      )}

      {/* Live Speech Waveform Bar when recording */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="flex items-center justify-between rounded-xl border border-primary/40 bg-primary/15 px-4 py-2.5 backdrop-blur-md"
          >
            <div className="flex items-center gap-3">
              <div className="relative flex h-3 w-3">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger opacity-75" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-danger" />
              </div>
              <span className="font-mono text-xs font-semibold text-white/90">
                Listening... Speak now
              </span>
              {/* Equalizing wave bars */}
              <div className="flex items-center gap-1">
                {[0.4, 0.8, 0.5, 1, 0.6, 0.9].map((delay, idx) => (
                  <motion.div
                    key={idx}
                    animate={{ scaleY: [0.3, 1.2, 0.3] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: delay * 0.2 }}
                    className="h-4 w-1 rounded-full bg-accent"
                  />
                ))}
              </div>
            </div>

            <button
              onClick={toggleRecording}
              className="rounded-lg bg-danger/20 border border-danger/40 px-3 py-1 text-xs font-semibold text-danger hover:bg-danger/30 transition-all"
            >
              Done Recording
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Composer Box */}
      <div className="composer-box relative flex flex-col gap-0">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); handleInput(); }}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder="Message Vikrm AI... (Enter to send, Shift+Enter for newline, paste files directly)"
          rows={1}
          disabled={disabled}
          className="max-h-48 min-h-[48px] flex-1 resize-none bg-transparent px-4 pt-3.5 pb-3 text-sm text-white placeholder:text-white/30 focus:outline-none disabled:opacity-50"
          style={{ overflow: "hidden" }}
        />

        {/* Emoji picker popover */}
        <AnimatePresence>
          {showEmojiPicker && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 10 }}
              className="absolute bottom-full left-4 mb-2 z-50 flex flex-wrap gap-2 rounded-2xl border border-border/80 bg-surface/95 p-3 backdrop-blur-2xl shadow-2xl max-w-xs"
            >
              {EMOJIS.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => {
                    setValue((prev) => prev + emoji);
                    setShowEmojiPicker(false);
                  }}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-lg hover:bg-white/10 transition-colors"
                >
                  {emoji}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Bottom toolbar */}
        <div className="flex items-center justify-between border-t border-border/40 px-3 py-2">
          <div className="flex items-center gap-1.5">
            {/* Attach button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex h-8 w-8 items-center justify-center rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all"
              title="Attach documents or images"
            >
              <Paperclip className="h-4 w-4" />
            </button>

            {/* Mic button with pulse ring animation */}
            <button
              onClick={toggleRecording}
              className={`relative flex h-8 w-8 items-center justify-center rounded-xl transition-all ${
                isRecording
                  ? "bg-danger text-white shadow-glow-sm"
                  : "text-white/40 hover:text-white hover:bg-white/5"
              }`}
              title="Voice recording (Web Speech API)"
            >
              <Mic className="h-4 w-4" />
            </button>

            {/* Emoji picker button */}
            <button
              onClick={() => setShowEmojiPicker((v) => !v)}
              className="flex h-8 w-8 items-center justify-center rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all"
              title="Insert emoji"
            >
              <Smile className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center gap-3">
            {charCount > 0 && (
              <span className="font-mono text-[10px] text-white/30">
                {wordCount} w · {charCount} c
              </span>
            )}
            <span className="hidden sm:inline font-mono text-[10px] text-white/25">
              Shift+Enter for newline
            </span>

            {/* Animated send/stop button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={disabled && onStop ? onStop : submit}
              disabled={!disabled && (!value.trim() && attachments.length === 0)}
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-all ${
                disabled && onStop
                  ? "bg-danger text-white hover:bg-danger/80 shadow-glow-sm cursor-pointer"
                  : "bg-gradient-brand text-white shadow-glow-sm disabled:opacity-30 disabled:shadow-none"
              }`}
              aria-label={disabled && onStop ? "Stop generation" : "Send message"}
              title={disabled && onStop ? "Stop generation" : "Send message"}
            >
              {disabled ? (
                onStop ? (
                  <Square className="h-3.5 w-3.5 fill-current text-white" />
                ) : (
                  <Loader2 className="h-4 w-4 animate-spin text-white" />
                )
              ) : (
                <Send className="h-4 w-4" strokeWidth={2} />
              )}
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
}
