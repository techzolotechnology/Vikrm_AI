import { useRef, useState, type KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, Mic, Paperclip } from "lucide-react";

interface ComposerProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

const SUGGESTIONS = [
  "Summarize key project findings",
  "Write an agent execution prompt",
  "Explain the local RAG pipeline",
  "List recent memory entries",
];

export function Composer({ onSend, disabled }: ComposerProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    // Reset textarea height
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
  const isNearLimit = charCount > 3500;

  return (
    <div className="flex flex-col gap-2.5">
      {/* Suggestion pills */}
      <AnimatePresence>
        {value.length === 0 && !disabled && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.2 }}
            className="flex flex-wrap items-center gap-1.5 px-1"
          >
            {SUGGESTIONS.map((suggestion, i) => (
              <motion.button
                key={suggestion}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => onSend(suggestion)}
                className="flex items-center gap-1.5 rounded-full border border-border/60 bg-surface/50 px-3 py-1.5 text-[11px] font-medium text-white/50 hover:border-primary/40 hover:bg-surface/80 hover:text-white/90 transition-all duration-200 backdrop-blur-sm"
              >
                <Sparkles className="h-3 w-3 text-accent" />
                <span>{suggestion}</span>
              </motion.button>
            ))}
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
          placeholder="Message Vikrm AI... (Enter to send, Shift+Enter for newline)"
          rows={1}
          disabled={disabled}
          className="max-h-44 min-h-[44px] flex-1 resize-none bg-transparent px-4 pt-3.5 pb-3 text-sm text-white placeholder:text-white/30 focus:outline-none disabled:opacity-50"
          style={{ overflow: "hidden" }}
        />

        {/* Bottom toolbar */}
        <div className="flex items-center justify-between border-t border-border/40 px-3 py-2">
          <div className="flex items-center gap-1.5">
            <button
              className="flex h-7 w-7 items-center justify-center rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
              title="Attach file"
            >
              <Paperclip className="h-3.5 w-3.5" />
            </button>
            <button
              className="flex h-7 w-7 items-center justify-center rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
              title="Voice input"
            >
              <Mic className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="flex items-center gap-2.5">
            {charCount > 0 && (
              <span className={`font-mono text-[10px] ${isNearLimit ? "text-warning" : "text-white/25"}`}>
                {charCount.toLocaleString()}
              </span>
            )}
            <span className="hidden sm:inline font-mono text-[10px] text-white/25">
              Shift+Enter for newline
            </span>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={submit}
              disabled={disabled || value.trim().length === 0}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-glow-sm transition-all disabled:opacity-30 disabled:shadow-none"
              aria-label="Send message"
            >
              {disabled ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="h-3.5 w-3.5 rounded-full border-2 border-white/30 border-t-white"
                />
              ) : (
                <Send className="h-3.5 w-3.5" strokeWidth={2} />
              )}
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
}
