import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Bot, Cpu, Thermometer, Palette, Sparkles } from "lucide-react";

import { useCreateAgent } from "@/hooks/use-agents";

const COLOR_OPTIONS = ["#7C3AED", "#22D3EE", "#22C55E", "#F59E0B", "#EF4444", "#EC4899", "#F97316", "#06B6D4"];

export function AgentForm({ onClose }: { onClose: () => void }) {
  const createAgent = useCreateAgent();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [goal, setGoal] = useState("");
  const [personality, setPersonality] = useState("");
  const [model, setModel] = useState("llama3.2");
  const [temperature, setTemperature] = useState(0.7);
  const [color, setColor] = useState(COLOR_OPTIONS[0]);

  const handleSubmit = () => {
    if (!name.trim()) return;
    createAgent.mutate(
      {
        name: name.trim(),
        description: description.trim() || undefined,
        instructions: instructions.trim() || undefined,
        goal: goal.trim() || undefined,
        personality: personality.trim() || undefined,
        provider: "ollama",
        model,
        temperature,
        avatar_color: color,
      },
      { onSuccess: onClose },
    );
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-6"
        style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(8px)" }}
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 20 }}
          transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
          className="glass-card w-full max-w-lg border border-border/80 shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
            <div className="flex items-center gap-3">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-xl text-base font-bold text-white transition-all"
                style={{ backgroundColor: color, boxShadow: `0 4px 16px ${color}40` }}
              >
                {name ? name.charAt(0).toUpperCase() : <Bot className="h-4 w-4" />}
              </div>
              <div>
                <h2 className="font-display text-base font-bold text-white">Create AI Agent</h2>
                <p className="text-[11px] text-white/40">Configure a new autonomous agent persona</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-border/60 text-white/40 hover:text-white hover:border-white/20 transition-all"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Body */}
          <div className="max-h-[60vh] overflow-y-auto no-scrollbar">
            <div className="space-y-4 p-6">
              {/* Name */}
              <Field label="Agent Name" required>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Research Assistant"
                  className="input text-sm"
                />
              </Field>

              {/* Description */}
              <Field label="Description">
                <input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Finds and summarizes information with citations"
                  className="input text-sm"
                />
              </Field>

              {/* Instructions */}
              <Field label="System Instructions" icon={<Sparkles className="h-3 w-3 text-accent" />}>
                <textarea
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="You are a meticulous research assistant who always cites sources..."
                  rows={3}
                  className="input resize-none text-sm"
                />
              </Field>

              {/* Goal */}
              <Field label="Goal">
                <input
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  placeholder="Provide accurate, well-cited answers"
                  className="input text-sm"
                />
              </Field>

              {/* Personality */}
              <Field label="Personality">
                <input
                  value={personality}
                  onChange={(e) => setPersonality(e.target.value)}
                  placeholder="Formal, precise, no filler"
                  className="input text-sm"
                />
              </Field>

              {/* Model */}
              <Field label="Model" icon={<Cpu className="h-3 w-3 text-accent/60" />}>
                <input
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="llama3.2"
                  className="input text-sm font-mono"
                />
              </Field>

              {/* Temperature */}
              <Field label={`Temperature: ${temperature.toFixed(1)}`} icon={<Thermometer className="h-3 w-3 text-warning/60" />}>
                <div className="mt-2 space-y-1.5">
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={temperature}
                    onChange={(e) => setTemperature(Number(e.target.value))}
                    className="w-full accent-primary"
                  />
                  <div className="flex justify-between font-mono text-[10px] text-white/30">
                    <span>Focused (0)</span>
                    <span>Balanced (1)</span>
                    <span>Creative (2)</span>
                  </div>
                </div>
              </Field>

              {/* Memory & Knowledge Base */}
              <Field label="Persistent Memory" icon={<Sparkles className="h-3 w-3 text-accent" />}>
                <div className="mt-1 flex items-center justify-between rounded-xl border border-border/60 bg-surface/40 p-3">
                  <div>
                    <div className="text-xs font-semibold text-white">Enable Vector Memory</div>
                    <div className="text-[10px] text-white/40">Allows agent to recall previous chat context</div>
                  </div>
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 rounded accent-primary bg-background border-border"
                  />
                </div>
              </Field>

              {/* Color */}
              <Field label="Avatar Color" icon={<Palette className="h-3 w-3 text-white/40" />}>
                <div className="mt-2 flex gap-2.5">
                  {COLOR_OPTIONS.map((option) => (
                    <button
                      key={option}
                      type="button"
                      onClick={() => setColor(option)}
                      className="relative h-8 w-8 rounded-full transition-all hover:scale-110"
                      style={{
                        backgroundColor: option,
                        boxShadow: color === option ? `0 0 12px ${option}60, 0 0 0 2px ${option}` : "none",
                      }}
                      aria-label={`Choose color ${option}`}
                    >
                      {color === option && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="h-2 w-2 rounded-full bg-white/80" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </Field>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center gap-3 border-t border-border/50 px-6 py-4">
            <button
              onClick={onClose}
              className="flex-1 rounded-xl border border-border/60 py-2.5 text-sm font-medium text-white/60 hover:text-white hover:border-white/20 transition-all"
            >
              Cancel
            </button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSubmit}
              disabled={!name.trim() || createAgent.isPending}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-gradient-brand py-2.5 text-sm font-bold text-white shadow-glow-sm disabled:opacity-40 transition-all"
            >
              {createAgent.isPending ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white"
                  />
                  Creating...
                </>
              ) : (
                <>
                  <Bot className="h-4 w-4" />
                  Create Agent
                </>
              )}
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function Field({ label, required, icon, children }: { label: string; required?: boolean; icon?: ReactNode; children: ReactNode }) {
  return (
    <label className="block">
      <div className="mb-1.5 flex items-center gap-1.5">
        {icon}
        <span className="text-xs font-medium text-white/50">
          {label}
          {required && <span className="ml-1 text-primary">*</span>}
        </span>
      </div>
      {children}
    </label>
  );
}
