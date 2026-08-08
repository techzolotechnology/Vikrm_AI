import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { X, Sliders, Info, Trash2, Sparkles } from "lucide-react";

import { useAgents } from "@/hooks/use-agents";
import { useProviders } from "@/hooks/use-providers";
import { useTools } from "@/hooks/use-workflows";
import type { WorkflowNode, WorkflowNodeData } from "@/types/workflow";

const OPERATORS = [
  "equals",
  "not_equals",
  "contains",
  "not_contains",
  "greater_than",
  "less_than",
  "is_empty",
  "is_not_empty",
];

interface NodeConfigPanelProps {
  node: WorkflowNode;
  onChange: (data: WorkflowNodeData) => void;
  onClose: () => void;
  onDelete: () => void;
}

export function NodeConfigPanel({ node, onChange, onClose, onDelete }: NodeConfigPanelProps) {
  const { data: agents = [] } = useAgents();
  const { data: tools = [] } = useTools();
  const { providerModels, providerList } = useProviders();
  const [activeTab, setActiveTab] = useState<"config" | "help">("config");

  const set = (patch: Partial<WorkflowNodeData>) => onChange({ ...node.data, ...patch });

  return (
    <motion.div
      initial={{ opacity: 0, x: 20, scale: 0.96 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.96 }}
      transition={{ duration: 0.2 }}
      className="glass-card-elevated absolute right-4 top-20 z-20 w-80 space-y-4 p-5 shadow-2xl backdrop-blur-2xl border border-border/80"
    >
      <div className="flex items-center justify-between border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-primary/20 text-accent font-mono text-xs font-bold">
            ⚡
          </span>
          <div>
            <h3 className="font-display text-sm font-bold text-white capitalize">{node.type} Node Settings</h3>
            <span className="font-mono text-[10px] text-white/40">Node ID #{node.id}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-white/40 hover:bg-white/10 hover:text-white transition"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex rounded-xl bg-background/50 p-1 font-mono text-xs border border-border/60">
        <button
          onClick={() => setActiveTab("config")}
          className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-1 transition ${
            activeTab === "config" ? "bg-primary/20 text-white font-semibold shadow-sm" : "text-white/40 hover:text-white"
          }`}
        >
          <Sliders className="h-3 w-3" /> Parameters
        </button>
        <button
          onClick={() => setActiveTab("help")}
          className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg py-1 transition ${
            activeTab === "help" ? "bg-primary/20 text-white font-semibold shadow-sm" : "text-white/40 hover:text-white"
          }`}
        >
          <Info className="h-3 w-3" /> Reference
        </button>
      </div>

      {activeTab === "config" ? (
        <div className="space-y-3.5 max-h-[calc(100vh-280px)] overflow-y-auto no-scrollbar pr-0.5">
          {node.type === "llm" && (
            <>
              <Field label="Prompt Template (Supports {{input}} or {{node_id.output}})">
                <textarea
                  value={node.data.prompt ?? ""}
                  onChange={(e) => set({ prompt: e.target.value })}
                  rows={3}
                  className="input resize-none text-xs font-mono bg-background/60"
                  placeholder="Enter system prompt template..."
                />
              </Field>
              <Field label="Model Provider">
                <select
                  value={node.data.provider ?? (providerList[0] || "ollama")}
                  onChange={(e) => {
                    const newProv = e.target.value;
                    const defaultM = providerModels[newProv]?.[0] ?? "qwen3:8b";
                    set({ provider: newProv, model: defaultM });
                  }}
                  className="input text-xs bg-background/60"
                >
                  {providerList.map((p) => (
                    <option key={p} value={p}>
                      {p.charAt(0).toUpperCase() + p.slice(1)} {p === "ollama" ? "(Local)" : ""}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Model Name">
                <select
                  value={node.data.model ?? "qwen3:8b"}
                  onChange={(e) => set({ model: e.target.value })}
                  className="input text-xs font-mono bg-background/60"
                >
                  {(providerModels[node.data.provider ?? "ollama"] || ["qwen3:8b"]).map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label={`Temperature: ${(node.data.temperature ?? 0.7).toFixed(1)}`}>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.1}
                  value={node.data.temperature ?? 0.7}
                  onChange={(e) => set({ temperature: Number(e.target.value) })}
                  className="w-full accent-primary"
                />
              </Field>
            </>
          )}

          {node.type === "agent" && (
            <>
              <Field label="Select Autonomous Agent">
                <select
                  value={node.data.agent_id ?? ""}
                  onChange={(e) => set({ agent_id: Number(e.target.value) })}
                  className="input text-xs bg-background/60"
                >
                  <option value="">Choose configured agent...</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      🤖 {a.name} ({a.provider}/{a.model})
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Task Prompt Override">
                <textarea
                  value={node.data.prompt ?? "{{input}}"}
                  onChange={(e) => set({ prompt: e.target.value })}
                  rows={3}
                  className="input resize-none text-xs font-mono bg-background/60"
                />
              </Field>
            </>
          )}

          {node.type === "condition" && (
            <>
              <Field label="Left Operand Expression">
                <input
                  value={node.data.left ?? "{{input}}"}
                  onChange={(e) => set({ left: e.target.value })}
                  className="input text-xs font-mono bg-background/60"
                />
              </Field>
              <Field label="Comparison Operator">
                <select
                  value={node.data.operator ?? "contains"}
                  onChange={(e) => set({ operator: e.target.value })}
                  className="input text-xs bg-background/60"
                >
                  {OPERATORS.map((op) => (
                    <option key={op} value={op}>
                      {op}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Right Operand Value">
                <input
                  value={node.data.right ?? ""}
                  onChange={(e) => set({ right: e.target.value })}
                  className="input text-xs font-mono bg-background/60"
                />
              </Field>
            </>
          )}

          {node.type === "tool" && (
            <>
              <Field label="Select Registered Tool">
                <select
                  value={node.data.tool_name ?? ""}
                  onChange={(e) => set({ tool_name: e.target.value })}
                  className="input text-xs bg-background/60"
                >
                  <option value="">Select tool...</option>
                  {tools.map((t) => (
                    <option key={t.name} value={t.name}>
                      🛠 {t.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Tool Input Argument">
                <textarea
                  value={node.data.input ?? "{{input}}"}
                  onChange={(e) => set({ input: e.target.value })}
                  rows={2}
                  className="input resize-none text-xs font-mono bg-background/60"
                />
              </Field>
            </>
          )}

          {node.type === "output" && (
            <Field label="Final Response Template">
              <textarea
                value={node.data.template ?? "{{input}}"}
                onChange={(e) => set({ template: e.target.value })}
                rows={3}
                className="input resize-none text-xs font-mono bg-background/60"
              />
            </Field>
          )}

          {node.type === "start" && (
            <div className="rounded-xl border border-success/30 bg-success/10 p-3 text-xs text-success flex items-center gap-2">
              <Sparkles className="h-4 w-4 shrink-0" />
              <span>Start Node initializes the execution context with the user payload.</span>
            </div>
          )}

          {node.type !== "start" && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onDelete}
              className="w-full flex items-center justify-center gap-1.5 rounded-xl border border-danger/40 bg-danger/10 py-2 text-xs font-bold text-danger hover:bg-danger/20 transition mt-4"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete Node
            </motion.button>
          )}
        </div>
      ) : (
        <div className="space-y-2.5 text-xs text-white/70 leading-relaxed font-mono">
          <p className="font-semibold text-accent">Templating Variables:</p>
          <ul className="space-y-1 text-[11px] text-white/50 list-disc pl-4">
            <li><code className="text-white">{`{{input}}`}</code> - Initial input payload</li>
            <li><code className="text-white">{`{{node_id.output}}`}</code> - Output of previous node</li>
            <li><code className="text-white">{`{{start.output}}`}</code> - Payload from start node</li>
          </ul>
        </div>
      )}
    </motion.div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-semibold text-white/60">{label}</span>
      {children}
    </label>
  );
}
