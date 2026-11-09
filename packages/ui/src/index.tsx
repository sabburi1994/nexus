import React from "react";

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
}) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm backdrop-blur transition hover:border-slate-700">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
      <div className="mt-2 flex items-baseline justify-between">
        <p className="text-2xl font-bold tracking-tight text-slate-50">{value}</p>
        {trendValue && (
          <span
            className={`inline-flex items-center text-xs font-medium ${
              trend === "up"
                ? "text-emerald-400"
                : trend === "down"
                ? "text-rose-400"
                : "text-slate-400"
            }`}
          >
            {trendValue}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};

export interface AiBadgeProps {
  model?: string;
  status?: "active" | "idle" | "error";
  thinkingLevel?: "low" | "medium" | "high";
}

export const AiBadge: React.FC<AiBadgeProps> = ({
  model = "Gemini 3.8 Flash",
  status = "active",
  thinkingLevel = "low",
}) => {
  const dotColor =
    status === "active"
      ? "bg-emerald-400"
      : status === "error"
      ? "bg-rose-400"
      : "bg-slate-400";

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-950/40 px-3 py-1 text-xs font-medium text-indigo-300">
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
      <span>{model}</span>
      <span className="rounded bg-indigo-900/60 px-1.5 py-0.2 text-[10px] text-indigo-400">
        {thinkingLevel} thinking
      </span>
    </div>
  );
};

export interface NexusHeaderProps {
  appName: string;
  tagline?: string;
  activeModel?: string;
  budgetSpentUsd?: number;
  budgetCapUsd?: number;
}

export const NexusHeader: React.FC<NexusHeaderProps> = ({
  appName,
  tagline = "Autonomous Agentic Application",
  activeModel = "Gemini 3.8 Flash",
  budgetSpentUsd = 0.0,
  budgetCapUsd = 1.0,
}) => {
  const pct = Math.min(100, (budgetSpentUsd / (budgetCapUsd || 1.0)) * 100);
  return (
    <header className="flex flex-wrap items-center justify-between border-b border-slate-800 bg-slate-950/90 px-6 py-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 font-bold text-white shadow-md shadow-indigo-500/20">
          NX
        </div>
        <div>
          <h1 className="text-base font-semibold text-slate-100">{appName}</h1>
          <p className="text-xs text-slate-400">{tagline}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <AiBadge model={activeModel} status="active" />
        <div className="hidden sm:block text-right">
          <p className="text-[11px] text-slate-400">Daily Spend</p>
          <p className="text-xs font-mono font-medium text-slate-200">
            ${budgetSpentUsd.toFixed(4)} / ${budgetCapUsd.toFixed(2)}
          </p>
        </div>
      </div>
    </header>
  );
};

export interface TraceStep {
  agentName: string;
  role: string;
  status: "completed" | "running" | "error" | "idle";
  costUsd: number;
  tokens: number;
  summary: string;
  timestamp: string;
}

export interface TraceViewerProps {
  steps: TraceStep[];
}

export const TraceViewer: React.FC<TraceViewerProps> = ({ steps }) => {
  return (
    <div className="space-y-3">
      {steps.map((step, idx) => (
        <div
          key={idx}
          className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs text-slate-300"
        >
          <div className="mt-0.5">
            {step.status === "completed" && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                ✓
              </span>
            )}
            {step.status === "running" && (
              <span className="flex h-4 w-4 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
            )}
            {step.status === "error" && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-rose-500/20 text-rose-400">
                ✗
              </span>
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200">{step.agentName}</span>
              <span className="font-mono text-[10px] text-slate-500">{step.timestamp}</span>
            </div>
            <p className="mt-1 text-slate-300">{step.summary}</p>
            <div className="mt-2 flex items-center gap-3 font-mono text-[10px] text-slate-400">
              <span>Tokens: {step.tokens.toLocaleString()}</span>
              <span>Cost: ${step.costUsd.toFixed(5)}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export interface SecurityShieldBadgeProps {
  injectionsBlocked?: number;
  piiScrubbed?: number;
}

export const SecurityShieldBadge: React.FC<SecurityShieldBadgeProps> = ({
  injectionsBlocked = 0,
  piiScrubbed = 0,
}) => {
  return (
    <div className="inline-flex items-center gap-2 rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-1.5 text-xs text-emerald-400">
      <span className="font-bold">🛡️ Shield Active</span>
      <span className="text-[10px] text-emerald-500">
        ({injectionsBlocked} attacks defused, {piiScrubbed} secrets scrubbed)
      </span>
    </div>
  );
};
