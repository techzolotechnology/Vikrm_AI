import type { ReactNode } from "react";
import { Handle, Position } from "@xyflow/react";
import { Bot, Flag, GitBranch, MessageSquare, Wrench, LogOut, Sparkles, CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { WorkflowNodeData } from "@/types/workflow";

interface NodeShellProps {
  icon: React.ElementType;
  label: string;
  color: string;
  badge?: string;
  summary: string;
  hasTarget?: boolean;
  hasSource?: boolean;
  selected?: boolean;
}

function NodeShell({
  icon: Icon,
  label,
  color,
  badge,
  summary,
  hasTarget = true,
  hasSource = true,
  selected,
  children,
}: NodeShellProps & { children?: ReactNode }) {
  return (
    <div
      className={cn(
        "relative min-w-[210px] rounded-2xl border bg-surface/90 p-3.5 shadow-2xl backdrop-blur-2xl transition-all duration-300 group",
        selected
          ? "border-primary shadow-glow-md scale-[1.02]"
          : "border-border/80 hover:border-primary/40 hover:shadow-glow-sm",
      )}
      style={{
        background: "linear-gradient(135deg, rgba(20,20,30,0.95) 0%, rgba(15,14,23,0.9) 100%)",
      }}
    >
      {/* Top accent glow line */}
      <div
        className="absolute inset-x-0 top-0 h-0.5 rounded-t-2xl opacity-60 transition-opacity group-hover:opacity-100"
        style={{ backgroundColor: color }}
      />

      {hasTarget && (
        <Handle
          type="target"
          position={Position.Left}
          className="!h-3.5 !w-3.5 !bg-surface !border-2 transition-transform hover:scale-125"
          style={{ borderColor: color }}
        />
      )}

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl transition-transform group-hover:scale-110 shadow-sm"
            style={{ backgroundColor: `${color}25`, border: `1px solid ${color}40` }}
          >
            <Icon className="h-4 w-4" style={{ color }} strokeWidth={2} />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-display text-xs font-bold text-white tracking-wide">{label}</span>
              {badge && (
                <span
                  className="rounded-full px-1.5 py-0.2 font-mono text-[9px] font-semibold"
                  style={{ backgroundColor: `${color}20`, color }}
                >
                  {badge}
                </span>
              )}
            </div>
            <p className="mt-0.5 max-w-[140px] truncate font-mono text-[10px] text-white/40">{summary}</p>
          </div>
        </div>
        <span className="h-2 w-2 rounded-full bg-success/80 shadow-glow-sm" title="Node Ready" />
      </div>

      {children}

      {hasSource && (
        <Handle
          type="source"
          position={Position.Right}
          className="!h-3.5 !w-3.5 !bg-surface !border-2 transition-transform hover:scale-125"
          style={{ borderColor: color }}
        />
      )}
    </div>
  );
}

export function StartNode({ selected }: { selected?: boolean }) {
  return (
    <NodeShell
      icon={Flag}
      label="Start Node"
      badge="ENTRY"
      color="#22C55E"
      summary="Trigger / Event Payload"
      hasTarget={false}
      selected={selected}
    >
      <div className="mt-2.5 flex items-center gap-1.5 rounded-lg border border-success/30 bg-success/10 px-2 py-1 text-[10px] font-mono text-success">
        <CheckCircle2 className="h-3 w-3 shrink-0" />
        <span>Receives {`{{input}}`} payload</span>
      </div>
    </NodeShell>
  );
}

export function LLMNode({ data, selected }: { data: WorkflowNodeData; selected?: boolean }) {
  return (
    <NodeShell
      icon={MessageSquare}
      label="LLM Provider"
      badge={data.provider ?? "ollama"}
      color="#7C3AED"
      summary={data.model ? `${data.model}` : "No model configured"}
      selected={selected}
    >
      {data.prompt && (
        <div className="mt-2.5 rounded-lg border border-white/10 bg-background/50 p-2 font-mono text-[10px] text-white/60 line-clamp-2">
          {data.prompt}
        </div>
      )}
    </NodeShell>
  );
}

export function AgentNode({ data, selected }: { data: WorkflowNodeData; selected?: boolean }) {
  return (
    <NodeShell
      icon={Bot}
      label="Autonomous Agent"
      badge="AGENT"
      color="#22D3EE"
      summary={data.agent_id ? `Assigned Agent #${data.agent_id}` : "Select agent in properties"}
      selected={selected}
    >
      <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-white/40 border-t border-border/40 pt-2">
        <span className="flex items-center gap-1 text-accent">
          <Sparkles className="h-3 w-3" /> Autonomous
        </span>
        <span>Memory Active</span>
      </div>
    </NodeShell>
  );
}

export function ConditionNode({ data, selected }: { data: WorkflowNodeData; selected?: boolean }) {
  return (
    <div
      className={cn(
        "relative min-w-[210px] rounded-2xl border bg-surface/90 p-3.5 shadow-2xl backdrop-blur-2xl transition-all duration-300 group",
        selected
          ? "border-primary shadow-glow-md scale-[1.02]"
          : "border-border/80 hover:border-warning/40 hover:shadow-glow-sm",
      )}
      style={{
        background: "linear-gradient(135deg, rgba(20,20,30,0.95) 0%, rgba(15,14,23,0.9) 100%)",
      }}
    >
      <div className="absolute inset-x-0 top-0 h-0.5 rounded-t-2xl bg-warning opacity-60 group-hover:opacity-100" />
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3.5 !w-3.5 !bg-surface !border-2 !border-warning"
      />
      <div className="flex items-center gap-2.5">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-warning/20 border border-warning/40">
          <GitBranch className="h-4 w-4 text-warning" strokeWidth={2} />
        </div>
        <div>
          <span className="font-display text-xs font-bold text-white tracking-wide">Logic Branch</span>
          <p className="mt-0.5 max-w-[130px] truncate font-mono text-[10px] text-white/40">
            {data.left && data.operator ? `${data.left} ${data.operator} ${data.right ?? ""}` : "Unconfigured"}
          </p>
        </div>
      </div>
      <div className="mt-3 flex justify-between border-t border-border/40 pt-2 text-[10px] font-mono">
        <span className="flex items-center gap-1 font-bold text-success">TRUE ↓</span>
        <span className="flex items-center gap-1 font-bold text-danger">FALSE ↓</span>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        style={{ left: "30%" }}
        className="!h-3.5 !w-3.5 !bg-success !border-2 !border-surface"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        style={{ left: "70%" }}
        className="!h-3.5 !w-3.5 !bg-danger !border-2 !border-surface"
      />
    </div>
  );
}

export function ToolNode({ data, selected }: { data: WorkflowNodeData; selected?: boolean }) {
  return (
    <NodeShell
      icon={Wrench}
      label="System Tool"
      badge="TOOL"
      color="#F59E0B"
      summary={data.tool_name ? String(data.tool_name) : "Select tool in properties"}
      selected={selected}
    />
  );
}

export function OutputNode({ data, selected }: { data: WorkflowNodeData; selected?: boolean }) {
  return (
    <NodeShell
      icon={LogOut}
      label="Final Output"
      badge="TERMINAL"
      color="#EC4899"
      summary={data.template ? String(data.template) : "{{input}}"}
      hasSource={false}
      selected={selected}
    />
  );
}

export const nodeTypes = {
  start: StartNode,
  llm: LLMNode,
  agent: AgentNode,
  condition: ConditionNode,
  tool: ToolNode,
  output: OutputNode,
};
