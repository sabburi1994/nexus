import React, { useState } from "react";

export type NexusTheme = "paper" | "dark";

export interface NexusNavItem {
  id: string;
  label: string;
  href?: string;
  active?: boolean;
  badge?: string;
}

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  accent?: "default" | "terracotta" | "emerald" | "cobalt";
  theme?: NexusTheme;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  accent = "default",
  theme = "paper",
}) => {
  const isPaper = theme === "paper";
  const topBar =
    accent === "terracotta"
      ? "border-t-2 border-t-[#bd513d]"
      : accent === "emerald"
      ? "border-t-2 border-t-[#0f7657]"
      : accent === "cobalt"
      ? "border-t-2 border-t-[#263aa8]"
      : "";

  const trendClasses =
    trend === "up"
      ? isPaper
        ? "border border-[#9ec9b8] bg-[#e6f4ee] text-[#0f7657]"
        : "bg-emerald-950/60 text-emerald-400 border border-emerald-800/50"
      : trend === "down"
      ? isPaper
        ? "border border-[#dfb1a6] bg-[#fbece7] text-[#a93f35]"
        : "bg-rose-950/60 text-rose-400 border border-rose-800/50"
      : isPaper
      ? "border border-[#d8d0c2] bg-[#f5f1e8] text-[#4e5b59]"
      : "bg-slate-800 text-slate-300 border border-slate-700";

  return (
    <div
      className={
        isPaper
          ? `rounded-lg border border-[#d6cec0] bg-[#fffdf8] p-5 shadow-[3px_3px_0_#ebe4d6] transition hover:border-[#1d2b30] ${topBar}`
          : `rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-sm transition hover:border-slate-700 ${topBar}`
      }
    >
      <p
        className={
          isPaper
            ? "text-[11px] font-semibold uppercase tracking-[0.11em] text-[#5e6a68]"
            : "text-xs font-semibold uppercase tracking-wider text-slate-400"
        }
      >
        {title}
      </p>
      <div className="mt-2.5 flex items-baseline justify-between gap-2">
        <p
          className={
            isPaper
              ? "font-mono text-2xl font-semibold tracking-tight text-[#172a2e] tabular-nums"
              : "font-mono text-2xl font-bold tracking-tight text-slate-50 tabular-nums"
          }
        >
          {value}
        </p>
        {trendValue && (
          <span className={`inline-flex items-center rounded px-2 py-0.5 text-[11px] font-medium ${trendClasses}`}>
            {trendValue}
          </span>
        )}
      </div>
      {subtitle && (
        <p className={isPaper ? "mt-1.5 text-xs text-[#606d6b]" : "mt-1 text-xs text-slate-400"}>{subtitle}</p>
      )}
    </div>
  );
};

export interface AiBadgeProps {
  model?: string;
  status?: "active" | "idle" | "error";
  thinkingLevel?: "low" | "medium" | "high";
  theme?: NexusTheme;
}

export const AiBadge: React.FC<AiBadgeProps> = ({
  model = "Gemini 3.8 Flash",
  status = "active",
  thinkingLevel = "low",
  theme = "paper",
}) => {
  const isPaper = theme === "paper";
  const dotColor =
    status === "active"
      ? isPaper
        ? "bg-[#0f7657]"
        : "bg-emerald-400"
      : status === "error"
      ? isPaper
        ? "bg-[#bd513d]"
        : "bg-rose-400"
      : "bg-slate-400";

  return (
    <div
      className={
        isPaper
          ? "inline-flex items-center gap-2 rounded-md border border-[#cbdbd7] bg-[#edf3f1] px-2.5 py-1 text-xs font-medium text-[#172a2e]"
          : "inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-950/40 px-3 py-1 text-xs font-medium text-indigo-300"
      }
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
      <span>{model}</span>
      <span
        className={
          isPaper
            ? "rounded border border-[#c3d3ce] bg-[#fffdf8] px-1.5 py-0.5 font-mono text-[10px] text-[#4b5c58]"
            : "rounded bg-indigo-900/60 px-1.5 py-0.5 text-[10px] text-indigo-400"
        }
      >
        {thinkingLevel}
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
  brandHref?: string;
  navItems?: NexusNavItem[];
  onNavSelect?: (id: string) => void;
  rightSlot?: React.ReactNode;
  theme?: NexusTheme;
}

export const NexusHeader: React.FC<NexusHeaderProps> = ({
  appName,
  tagline = "Autonomous Agentic Application",
  activeModel = "Gemini 3.8 Flash",
  budgetSpentUsd = 0.0,
  budgetCapUsd = 1.0,
  brandHref = "#overview",
  navItems,
  onNavSelect,
  rightSlot,
  theme = "paper",
}) => {
  const isPaper = theme === "paper";
  return (
    <header
      className={
        isPaper
          ? "sticky top-0 z-40 border-b border-[#c9d1cf] bg-[#fffdf8]/95 backdrop-blur-sm"
          : "sticky top-0 z-40 border-b border-slate-800 bg-slate-950/95 backdrop-blur-sm"
      }
    >
      <div className="h-[3px] w-full bg-gradient-to-r from-[#bd513d] via-[#172a2e] to-[#0f7657]" />
      <div className="mx-auto flex max-w-[1260px] flex-wrap items-center justify-between gap-4 px-5 py-3">
        <a
          href={brandHref}
          onClick={(e) => {
            if (onNavSelect && brandHref.startsWith("#")) {
              e.preventDefault();
              onNavSelect(brandHref.slice(1) || "overview");
            }
          }}
          className="flex items-center gap-3 text-left no-underline"
        >
          <div
            className={
              isPaper
                ? "flex h-9 w-9 items-center justify-center rounded-md border border-[#172a2e] bg-[#172a2e] font-mono text-xs font-bold tracking-wider text-[#fffdf8]"
                : "flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 font-bold text-white"
            }
          >
            NX
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={
                  isPaper
                    ? "text-base font-semibold tracking-tight text-[#172a2e]"
                    : "text-base font-semibold text-slate-100"
                }
              >
                {appName}
              </span>
            </div>
            <p className={isPaper ? "text-[11px] text-[#5e6a68]" : "text-xs text-slate-400"}>{tagline}</p>
          </div>
        </a>

        {navItems && navItems.length > 0 && (
          <nav aria-label="Workspace navigation" className="flex flex-wrap items-center gap-1">
            {navItems.map((item) => {
              const cls = item.active
                ? isPaper
                  ? "border border-[#172a2e] bg-[#172a2e] text-[#fffdf8]"
                  : "border border-indigo-500 bg-indigo-600 text-white"
                : isPaper
                ? "border border-transparent text-[#465452] hover:border-[#d6cec0] hover:bg-[#f2ede2] hover:text-[#172a2e]"
                : "border border-transparent text-slate-300 hover:bg-slate-900 hover:text-white";

              if (item.href && !onNavSelect) {
                return (
                  <a
                    key={item.id}
                    href={item.href}
                    className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${cls}`}
                  >
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="rounded bg-[#bd513d] px-1.5 py-0.5 font-mono text-[10px] text-white">
                        {item.badge}
                      </span>
                    )}
                  </a>
                );
              }
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavSelect?.(item.id)}
                  aria-current={item.active ? "page" : undefined}
                  className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${cls}`}
                >
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="rounded bg-[#bd513d] px-1.5 py-0.5 font-mono text-[10px] text-white">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        )}

        <div className="flex items-center gap-3">
          {rightSlot}
          <AiBadge model={activeModel} status="active" theme={theme} />
          <div className="hidden sm:block text-right">
            <p className={isPaper ? "text-[10px] uppercase tracking-wider text-[#62706d]" : "text-[11px] text-slate-400"}>
              Budget Cap
            </p>
            <p
              className={
                isPaper
                  ? "font-mono text-xs font-semibold text-[#172a2e] tabular-nums"
                  : "font-mono text-xs font-medium text-slate-200 tabular-nums"
              }
            >
              ${budgetSpentUsd.toFixed(4)} / ${budgetCapUsd.toFixed(2)}
            </p>
          </div>
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
  artifactPreview?: string;
}

export interface TraceViewerProps {
  steps: TraceStep[];
  theme?: NexusTheme;
}

export const TraceViewer: React.FC<TraceViewerProps> = ({ steps, theme = "paper" }) => {
  const isPaper = theme === "paper";
  return (
    <div className="space-y-2.5">
      {steps.map((step, idx) => (
        <div
          key={`${step.agentName}-${idx}`}
          className={
            isPaper
              ? "flex items-start gap-3 rounded-lg border border-[#d8d0c2] bg-[#fffdf8] p-3.5 text-xs text-[#2b3a3c]"
              : "flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs text-slate-300"
          }
        >
          <div className="mt-0.5 shrink-0">
            {step.status === "completed" && (
              <span
                className={
                  isPaper
                    ? "flex h-5 w-5 items-center justify-center rounded-full border border-[#9ec9b8] bg-[#e6f4ee] text-[#0f7657]"
                    : "flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400"
                }
              >
                <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M3.5 8.5 6.5 11.5 12.5 4.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
            )}
            {step.status === "running" && (
              <span
                className={
                  isPaper
                    ? "flex h-5 w-5 animate-spin rounded-full border-2 border-[#bd513d] border-t-transparent"
                    : "flex h-5 w-5 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent"
                }
              />
            )}
            {step.status === "error" && (
              <span
                className={
                  isPaper
                    ? "flex h-5 w-5 items-center justify-center rounded-full border border-[#dfb1a6] bg-[#fbece7] text-[#a93f35]"
                    : "flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/20 text-rose-400"
                }
              >
                <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M4.5 4.5 11.5 11.5M11.5 4.5 4.5 11.5" strokeLinecap="round" />
                </svg>
              </span>
            )}
            {step.status === "idle" && (
              <span className="flex h-5 w-5 items-center justify-center rounded-full border border-[#d6cec0] bg-[#f5f1e8] font-mono text-[10px] text-[#606d6b]">
                {String(idx + 1).padStart(2, "0")}
              </span>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className={isPaper ? "font-semibold text-[#172a2e]" : "font-semibold text-slate-200"}>
                  {step.agentName}
                </span>
                <span
                  className={
                    isPaper
                      ? "rounded border border-[#d8d0c2] bg-[#f5f1e8] px-1.5 py-0.5 text-[10px] font-medium text-[#52605d]"
                      : "rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400"
                  }
                >
                  {step.role}
                </span>
              </div>
              <span className={isPaper ? "font-mono text-[10px] text-[#667370]" : "font-mono text-[10px] text-slate-500"}>
                {step.timestamp}
              </span>
            </div>
            <p className={isPaper ? "mt-1.5 leading-relaxed text-[#394748]" : "mt-1 text-slate-300"}>{step.summary}</p>
            <div
              className={
                isPaper
                  ? "mt-2 flex flex-wrap items-center gap-3 font-mono text-[10px] text-[#5e6a68] tabular-nums"
                  : "mt-2 flex flex-wrap items-center gap-3 font-mono text-[10px] text-slate-400 tabular-nums"
              }
            >
              <span>Tokens: {step.tokens.toLocaleString()}</span>
              <span>Cost: ${step.costUsd.toFixed(6)}</span>
              {step.artifactPreview && (
                <span
                  className={
                    isPaper
                      ? "rounded bg-[#edf3f1] px-1.5 py-0.5 text-[#172a2e]"
                      : "rounded bg-slate-800 px-1.5 py-0.5 text-indigo-300"
                  }
                >
                  {step.artifactPreview}
                </span>
              )}
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
  theme?: NexusTheme;
}

export const SecurityShieldBadge: React.FC<SecurityShieldBadgeProps> = ({
  injectionsBlocked = 0,
  piiScrubbed = 0,
  theme = "paper",
}) => {
  const isPaper = theme === "paper";
  return (
    <div
      className={
        isPaper
          ? "inline-flex items-center gap-2 rounded-md border border-[#9ec9b8] bg-[#e6f4ee] px-3 py-1.5 text-xs text-[#0f5c43]"
          : "inline-flex items-center gap-2 rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-1.5 text-xs text-emerald-400"
      }
    >
      <svg viewBox="0 0 20 20" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path
          d="M10 2.5 16.5 5v4.8c0 4-2.8 6.8-6.5 7.7-3.7-.9-6.5-3.7-6.5-7.7V5L10 2.5Z"
          strokeLinejoin="round"
        />
        <path d="m7.2 10 2 2 3.8-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="font-semibold">Guardrail Shield Active</span>
      <span className={isPaper ? "font-mono text-[11px] text-[#0f7657]" : "font-mono text-[11px] text-emerald-500"}>
        ({injectionsBlocked} injections blocked, {piiScrubbed} secrets scrubbed)
      </span>
    </div>
  );
};

export interface HealingAttemptItem {
  attemptNumber: number;
  testFailures: string[];
  diagnosis: string;
  diffApplied: string;
  retestPassed: boolean;
  timestamp: string;
}

export interface HealingLoopPanelProps {
  report: {
    initialTestsPassed: boolean;
    totalAttempts: number;
    maxAttemptsAllowed: number;
    finalStatus: "HEALTHY" | "HEALED" | "EXHAUSTED";
    attempts: HealingAttemptItem[];
    durationSeconds: number;
    summary: string;
  };
  theme?: NexusTheme;
}

export const HealingLoopPanel: React.FC<HealingLoopPanelProps> = ({ report, theme = "paper" }) => {
  const isPaper = theme === "paper";
  const badgeStyle =
    report.finalStatus === "HEALED" || report.finalStatus === "HEALTHY"
      ? isPaper
        ? "border-[#9ec9b8] bg-[#e6f4ee] text-[#0f7657]"
        : "border-emerald-700/50 bg-emerald-950/50 text-emerald-300"
      : isPaper
      ? "border-[#dfb1a6] bg-[#fbece7] text-[#a93f35]"
      : "border-rose-700/50 bg-rose-950/50 text-rose-300";

  return (
    <div
      className={
        isPaper
          ? "rounded-lg border border-[#d6cec0] bg-[#fffdf8] p-5 shadow-[3px_3px_0_#ebe4d6]"
          : "rounded-xl border border-slate-800 bg-slate-900/70 p-5"
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e5ddd0] pb-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.11em] text-[#bd513d]">
            Stage 1 · Closed-Loop Self-Healing
          </p>
          <h3 className={isPaper ? "mt-0.5 text-base font-semibold text-[#172a2e]" : "mt-0.5 text-base font-semibold text-white"}>
            Autonomous QA → Patch → Retest Loop
          </h3>
        </div>
        <span className={`rounded border px-2.5 py-1 font-mono text-xs font-semibold ${badgeStyle}`}>
          {report.finalStatus} ({report.totalAttempts}/{report.maxAttemptsAllowed} cycles)
        </span>
      </div>

      <p className={isPaper ? "mt-3 text-sm text-[#394748]" : "mt-3 text-sm text-slate-300"}>{report.summary}</p>

      {report.attempts.length > 0 && (
        <div className="mt-4 space-y-3">
          {report.attempts.map((attempt) => (
            <div
              key={attempt.attemptNumber}
              className={
                isPaper
                  ? "rounded-md border border-[#d8d0c2] bg-[#f8f4ec] p-3.5 text-xs"
                  : "rounded-lg border border-slate-800 bg-slate-950/70 p-3.5 text-xs"
              }
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className={isPaper ? "font-mono font-semibold text-[#172a2e]" : "font-mono font-semibold text-slate-100"}>
                  Cycle #{attempt.attemptNumber} Diagnosis
                </span>
                <span
                  className={
                    attempt.retestPassed
                      ? "font-mono font-semibold text-[#0f7657]"
                      : "font-mono font-semibold text-[#bd513d]"
                  }
                >
                  {attempt.retestPassed ? "Retest PASSED" : "Retest FAILED"}
                </span>
              </div>
              <p className={isPaper ? "mt-1.5 text-[#394748]" : "mt-1.5 text-slate-300"}>{attempt.diagnosis}</p>
              {attempt.testFailures.length > 0 && (
                <ul className="mt-2 list-disc pl-4 font-mono text-[11px] text-[#a93f35]">
                  {attempt.testFailures.map((fail, i) => (
                    <li key={i}>{fail}</li>
                  ))}
                </ul>
              )}
              {attempt.diffApplied && (
                <pre className="mt-2.5 overflow-x-auto rounded border border-[#1d2b30] bg-[#142025] p-3 font-mono text-[11px] text-[#eaf1f0]">
                  {attempt.diffApplied}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export interface BlastRadiusCardProps {
  blastRadius: {
    target: string;
    riskTier: "LOW" | "MEDIUM" | "HIGH";
    directDependents: string[];
    indirectDependents: string[];
    affectedRoutes: string[];
    affectedTests: string[];
    totalAffectedFiles: number;
  };
  onSelectFile?: (file: string) => void;
  theme?: NexusTheme;
}

export const BlastRadiusCard: React.FC<BlastRadiusCardProps> = ({
  blastRadius,
  onSelectFile,
  theme = "paper",
}) => {
  const isPaper = theme === "paper";
  const riskBadge =
    blastRadius.riskTier === "HIGH"
      ? "border-[#dfb1a6] bg-[#fbece7] text-[#a93f35]"
      : blastRadius.riskTier === "MEDIUM"
      ? "border-[#dfbf70] bg-[#f9edcb] text-[#8a5a0a]"
      : "border-[#9ec9b8] bg-[#e6f4ee] text-[#0f7657]";

  return (
    <div
      className={
        isPaper
          ? "rounded-lg border border-[#d6cec0] bg-[#fffdf8] p-5 shadow-[3px_3px_0_#ebe4d6]"
          : "rounded-xl border border-slate-800 bg-slate-900/70 p-5"
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e5ddd0] pb-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.11em] text-[#263aa8]">
            Stage 2 · AST Blast Radius
          </p>
          <h3 className={isPaper ? "mt-0.5 font-mono text-sm font-semibold text-[#172a2e]" : "mt-0.5 font-mono text-sm font-semibold text-white"}>
            Target: {blastRadius.target}
          </h3>
        </div>
        <span className={`rounded border px-2.5 py-1 font-mono text-xs font-bold ${riskBadge}`}>
          {blastRadius.riskTier} RISK · {blastRadius.totalAffectedFiles} impacted
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#5e6a68]">
            Direct Dependents ({blastRadius.directDependents.length})
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {blastRadius.directDependents.length === 0 ? (
              <span className="text-xs text-[#707d7a]">None</span>
            ) : (
              blastRadius.directDependents.map((dep) => (
                <button
                  key={dep}
                  type="button"
                  onClick={() => onSelectFile?.(dep)}
                  className="rounded border border-[#c9d1cf] bg-[#f1f4f2] px-2 py-1 font-mono text-[11px] text-[#172a2e] transition hover:border-[#bd513d] hover:text-[#bd513d]"
                >
                  {dep}
                </button>
              ))
            )}
          </div>
        </div>

        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#5e6a68]">
            Indirect Dependents ({blastRadius.indirectDependents.length})
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {blastRadius.indirectDependents.length === 0 ? (
              <span className="text-xs text-[#707d7a]">None</span>
            ) : (
              blastRadius.indirectDependents.map((dep) => (
                <button
                  key={dep}
                  type="button"
                  onClick={() => onSelectFile?.(dep)}
                  className="rounded border border-[#d8d0c2] bg-[#f8f4ec] px-2 py-1 font-mono text-[11px] text-[#47534e] transition hover:border-[#263aa8]"
                >
                  {dep}
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 border-t border-[#ece4d7] pt-3 md:grid-cols-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#5e6a68]">Affected API Routes</p>
          <ul className="mt-1.5 space-y-1 font-mono text-[11px] text-[#263aa8]">
            {blastRadius.affectedRoutes.length === 0 ? (
              <li className="text-[#707d7a]">No FastAPI routes exposed</li>
            ) : (
              blastRadius.affectedRoutes.map((route, i) => <li key={i}>{route}</li>)
            )}
          </ul>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#5e6a68]">Regression Tests to Run</p>
          <ul className="mt-1.5 space-y-1 font-mono text-[11px] text-[#0f7657]">
            {blastRadius.affectedTests.length === 0 ? (
              <li className="text-[#bd513d]">0 matching tests detected — add regression coverage</li>
            ) : (
              blastRadius.affectedTests.map((t, i) => <li key={i}>{t}</li>)
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export interface RoiScorecardProps {
  roi: {
    projectName: string;
    totalFilesAnalyzed: number;
    totalLinesOfCode: number;
    totalInputTokens: number;
    totalOutputTokens: number;
    totalTokenCostUsd: number;
    engineeringHoursSaved: number;
    hourlyRateUsd: number;
    humanCostSavedUsd: number;
    netSavingsUsd: number;
    roiMultiplier: number;
    doraMetrics: {
      deploymentFrequencyMultiplier: number;
      leadTimeReductionPct: number;
      changeFailureRatePct: number;
      mttrMinutes: number;
    };
    vulnerabilitiesPrevented: number;
    healingCyclesExecuted: number;
    summary: string;
  };
  theme?: NexusTheme;
}

export const RoiScorecard: React.FC<RoiScorecardProps> = ({ roi, theme = "paper" }) => {
  const isPaper = theme === "paper";
  return (
    <div
      className={
        isPaper
          ? "rounded-lg border border-[#d6cec0] bg-[#fffdf8] p-5 shadow-[3px_3px_0_#ebe4d6]"
          : "rounded-xl border border-slate-800 bg-slate-900/70 p-5"
      }
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e5ddd0] pb-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.11em] text-[#0f7657]">
            Stage 3 · Enterprise ROI & DORA Telemetry
          </p>
          <h3 className={isPaper ? "mt-0.5 text-base font-semibold text-[#172a2e]" : "mt-0.5 text-base font-semibold text-white"}>
            {roi.projectName} Scorecard
          </h3>
        </div>
        <span className="rounded border border-[#9ec9b8] bg-[#e6f4ee] px-2.5 py-1 font-mono text-xs font-bold text-[#0f7657]">
          {roi.roiMultiplier.toLocaleString()}x Net ROI
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          title="Hours Saved"
          value={`${roi.engineeringHoursSaved.toFixed(1)}h`}
          subtitle={`${roi.totalFilesAnalyzed} files · ${roi.totalLinesOfCode.toLocaleString()} LOC`}
          theme={theme}
        />
        <StatCard
          title="Net Savings"
          value={`$${roi.netSavingsUsd.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
          subtitle={`At $${roi.hourlyRateUsd.toFixed(0)}/hr benchmark`}
          accent="emerald"
          theme={theme}
        />
        <StatCard
          title="LLM Token Cost"
          value={`$${roi.totalTokenCostUsd.toFixed(4)}`}
          subtitle={`${(roi.totalInputTokens + roi.totalOutputTokens).toLocaleString()} tokens`}
          accent="terracotta"
          theme={theme}
        />
        <StatCard
          title="Deploy Velocity"
          value={`${roi.doraMetrics.deploymentFrequencyMultiplier.toFixed(1)}x`}
          subtitle={`${roi.doraMetrics.leadTimeReductionPct.toFixed(0)}% shorter lead time`}
          accent="cobalt"
          theme={theme}
        />
      </div>

      <p className={isPaper ? "mt-4 rounded border border-[#e5ddd0] bg-[#f8f4ec] p-3 text-xs leading-relaxed text-[#394748]" : "mt-4 text-xs text-slate-300"}>
        {roi.summary}
      </p>
    </div>
  );
};

export interface CommandBlockProps {
  code: string;
  title?: string;
  language?: string;
}

export const CommandBlock: React.FC<CommandBlockProps> = ({ code, title, language = "bash" }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="overflow-hidden rounded-lg border border-[#1d2b30] bg-[#142025] text-[#eaf1f0] shadow-[3px_3px_0_#d8d0c2]">
      <div className="flex items-center justify-between border-b border-[#293a40] bg-[#1b2a30] px-4 py-2 text-[11px]">
        <div className="flex items-center gap-2 font-mono text-[#b7c8c5]">
          <span>{title || language}</span>
          {title && <span className="rounded bg-[#263940] px-1.5 py-0.5 text-[10px] text-[#8fa6a2]">{language}</span>}
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded border border-[#3a4f57] bg-[#22333a] px-2 py-0.5 font-mono text-[10px] text-[#eaf1f0] transition hover:border-[#bd513d] hover:bg-[#bd513d]"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-[#eaf1f0]">
        <code>{code}</code>
      </pre>
    </div>
  );
};
