import { motion } from "framer-motion";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { StatusBreakdown } from "@/types/analytics";

interface RunStatusChartProps {
  title: string;
  data: StatusBreakdown;
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; fill: string }> }) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-border/80 bg-surface/95 px-3 py-2 shadow-2xl backdrop-blur-2xl">
        <p className="font-mono text-xs text-white/80">
          {payload[0].name}: <span className="font-bold text-white">{payload[0].value}</span>
        </p>
      </div>
    );
  }
  return null;
};

export function RunStatusChart({ title, data }: RunStatusChartProps) {
  const chartData = [
    { name: "Completed", value: data.completed, color: "#22C55E" },
    { name: "Failed", value: data.failed, color: "#EF4444" },
    { name: "Running", value: data.running, color: "#F59E0B" },
  ];

  const total = data.completed + data.failed + data.running;
  const successRate = total > 0 ? Math.round((data.completed / total) * 100) : 0;

  return (
    <motion.div
      whileHover={{ y: -3 }}
      className="glass-card group relative overflow-hidden border border-border/70 p-5 hover:border-primary/20 transition-all duration-300"
    >
      {/* Background glow */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl"
        style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(34,197,94,0.06) 0%, transparent 60%)" }}
      />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-display text-xs font-semibold text-white/70">{title}</h3>
          <span className="font-mono text-[10px] text-white/30">{total} runs</span>
        </div>

        {total > 0 && (
          <div className="flex items-baseline gap-1 mb-3">
            <span className="font-display text-2xl font-bold text-success">{successRate}%</span>
            <span className="font-mono text-[10px] text-white/30">success rate</span>
          </div>
        )}

        {total === 0 ? (
          <div className="flex h-24 items-center justify-center">
            <p className="text-center text-xs text-white/25">No runs recorded yet.</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 12, top: 0, bottom: 0 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10, fontFamily: "JetBrains Mono" }}
                width={70}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={12}>
                {chartData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={entry.color}
                    fillOpacity={0.85}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </motion.div>
  );
}
