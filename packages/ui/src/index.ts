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
}

export const AiBadge: React.FC<AiBadgeProps> = ({
  model = "Gemini 3.8 Flash",
  status = "active",
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
    </div>
  );
};
