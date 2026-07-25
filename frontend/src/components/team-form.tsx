import { useState } from "react";
import { X } from "lucide-react";

import { useAgents } from "@/hooks/use-agents";
import { useCreateAgentTeam } from "@/hooks/use-agent-teams";

export function TeamForm({ onClose }: { onClose: () => void }) {
  const { data: agents = [] } = useAgents();
  const createTeam = useCreateAgentTeam();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [managerAgentId, setManagerAgentId] = useState<string>("");
  const [memberAgentIds, setMemberAgentIds] = useState<number[]>([]);

  const toggleMember = (agentId: number) => {
    setMemberAgentIds((prev) =>
      prev.includes(agentId) ? prev.filter((id) => id !== agentId) : [...prev, agentId],
    );
  };

  const handleSubmit = () => {
    if (!name.trim() || !managerAgentId || memberAgentIds.length === 0) return;
    createTeam.mutate(
      {
        name: name.trim(),
        description: description.trim() || undefined,
        manager_agent_id: Number(managerAgentId),
        member_agent_ids: memberAgentIds,
      },
      { onSuccess: onClose },
    );
  };

  const availableMembers = agents.filter((a) => String(a.id) !== managerAgentId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6">
      <div className="glass-card w-full max-w-md space-y-4 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold text-white">Create Team</h2>
          <button onClick={onClose} className="text-white/40 hover:text-white">
            <X className="h-5 w-5" strokeWidth={1.75} />
          </button>
        </div>

        {agents.length < 2 && (
          <p className="rounded-lg border border-warning/30 bg-warning/5 px-3 py-2 text-xs text-warning">
            You need at least 2 agents (one manager, one member) — create some on the Agents page first.
          </p>
        )}

        <label className="block">
          <span className="mb-1 block text-xs font-medium text-white/50">Team name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} className="input" />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-medium text-white/50">Description</span>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-medium text-white/50">Manager agent</span>
          <select
            value={managerAgentId}
            onChange={(e) => {
              setManagerAgentId(e.target.value);
              setMemberAgentIds((prev) => prev.filter((id) => String(id) !== e.target.value));
            }}
            className="input"
          >
            <option value="">Select the coordinating agent…</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>

        <div>
          <span className="mb-2 block text-xs font-medium text-white/50">Member agents</span>
          <div className="space-y-1.5">
            {availableMembers.map((agent) => (
              <label
                key={agent.id}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-background/40 px-3 py-2 text-sm text-white/70"
              >
                <input
                  type="checkbox"
                  checked={memberAgentIds.includes(agent.id)}
                  onChange={() => toggleMember(agent.id)}
                  className="accent-primary"
                />
                {agent.name}
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!name.trim() || !managerAgentId || memberAgentIds.length === 0 || createTeam.isPending}
          className="w-full rounded-xl bg-gradient-brand py-2.5 text-sm font-medium text-white disabled:opacity-40"
        >
          {createTeam.isPending ? "Creating…" : "Create Team"}
        </button>
      </div>
    </div>
  );
}
