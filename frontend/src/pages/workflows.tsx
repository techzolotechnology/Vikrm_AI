import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Workflow as WorkflowIcon, Clock, GitBranch, Play, ArrowUpRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { EmptyState } from "@/components/empty-state";
import { PageTransition } from "@/components/page-transition";
import { useCreateWorkflow, useDeleteWorkflow, useWorkflows } from "@/hooks/use-workflows";

const BLANK_DEFINITION = {
  nodes: [{ id: "start", type: "start" as const, data: {}, position: { x: 50, y: 150 } }],
  edges: [],
};

export function Workflows() {
  const { data: workflows = [], isLoading } = useWorkflows();
  const createWorkflow = useCreateWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const navigate = useNavigate();

  const handleCreate = () => {
    createWorkflow.mutate(
      { name: "Untitled Workflow", definition: BLANK_DEFINITION },
      { onSuccess: (workflow) => navigate(`/workflows/${workflow.id}`) },
    );
  };

  return (
    <PageTransition>
      <div className="aurora-bg min-h-screen bg-background px-8 py-8 md:px-12">
        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="page-icon-wrap">
              <WorkflowIcon className="h-5 w-5 text-cyan-400" strokeWidth={1.75} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-mono text-[10px] uppercase tracking-widest text-white/30">
                  Automation Engine
                </span>
              </div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white">
                Workflows
              </h1>
              <p className="text-sm text-white/40">
                Visual DAG pipelines for multi-step agent and tool execution.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {workflows.length > 0 && (
              <span className="font-mono text-[11px] text-white/30">
                {workflows.length} workflow{workflows.length !== 1 ? "s" : ""}
              </span>
            )}
            <motion.button
              whileHover={{ scale: 1.03, y: -1 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleCreate}
              disabled={createWorkflow.isPending}
              className="flex items-center gap-2 rounded-xl bg-gradient-brand px-4 py-2.5 text-xs font-bold text-white shadow-glow-sm disabled:opacity-50 transition-all"
            >
              {createWorkflow.isPending ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white"
                />
              ) : (
                <Plus className="h-4 w-4" strokeWidth={2} />
              )}
              New Workflow
            </motion.button>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card h-44 skeleton" />
            ))}
          </div>
        )}

        {/* Empty */}
        {!isLoading && workflows.length === 0 && (
          <EmptyState
            icon={WorkflowIcon}
            title="No Workflows Created"
            description="Build DAG execution graphs combining LLM nodes, condition branches, and tools into automated pipelines."
            actionLabel="Create First Workflow"
            onAction={handleCreate}
          />
        )}

        {/* Workflow Grid */}
        {!isLoading && workflows.length > 0 && (
          <AnimatePresence>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {workflows.map((workflow, index) => (
                <motion.div
                  key={workflow.id}
                  initial={{ opacity: 0, y: 16, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  whileHover={{ y: -5 }}
                  transition={{ delay: index * 0.06, duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
                  onClick={() => navigate(`/workflows/${workflow.id}`)}
                  className="glass-card group relative overflow-hidden flex flex-col border border-border/70 hover:border-cyan-400/30 cursor-pointer transition-all duration-300"
                >
                  {/* Top shimmer */}
                  <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  {/* Background glow */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
                    style={{ background: "radial-gradient(ellipse at 20% 20%, rgba(34,211,238,0.08) 0%, transparent 65%)" }}
                  />

                  <div className="relative z-10 p-5 flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 border border-cyan-400/20">
                        <WorkflowIcon className="h-5 w-5 text-cyan-400" strokeWidth={1.75} />
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/workflows/${workflow.id}`);
                          }}
                          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/30 hover:text-success hover:border-success/30 transition-all"
                          title="Run workflow"
                        >
                          <Play className="h-3 w-3" strokeWidth={2} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteWorkflow.mutate(workflow.id);
                          }}
                          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/60 bg-surface/60 text-white/30 hover:text-danger hover:border-danger/30 transition-all"
                          aria-label="Delete workflow"
                        >
                          <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                        </button>
                      </div>
                    </div>

                    <h3 className="font-display text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">
                      {workflow.name}
                    </h3>
                    {workflow.description ? (
                      <p className="mt-1.5 text-xs text-white/45 line-clamp-2 leading-relaxed">
                        {workflow.description}
                      </p>
                    ) : (
                      <p className="mt-1.5 text-xs italic text-white/25">No description</p>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="relative z-10 border-t border-border/40 px-5 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1.5 text-[10px] font-mono text-cyan-400/70">
                        <GitBranch className="h-3 w-3" strokeWidth={1.75} />
                        {workflow.definition.nodes.length} nodes
                      </div>
                      <div className="flex items-center gap-1.5 text-[10px] font-mono text-white/35">
                        <Clock className="h-3 w-3" strokeWidth={1.75} />
                        {workflow.definition.edges.length} edges
                      </div>
                    </div>
                    <ArrowUpRight className="h-3.5 w-3.5 text-white/20 group-hover:text-cyan-400/60 transition-colors" />
                  </div>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </PageTransition>
  );
}
