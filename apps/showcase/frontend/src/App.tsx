import React, { useState } from "react";
import {
  NexusHeader,
  AiBadge,
  StatCard,
  TraceViewer,
  SecurityShieldBadge,
  TraceStep,
} from "@nexus/ui";

interface Report {
  id: string;
  target: string;
  sector: string;
  sentiment_score: number;
  risk_level: string;
  summary: string;
  model: string;
  tokens_used: number;
}

export default function App() {
  const [target, setTarget] = useState("");
  const [sector, setSector] = useState("Macro");
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState<Report[]>([
    {
      id: "rep_init_1",
      target: "European Energy Grid Transition",
      sector: "Energy",
      sentiment_score: 82.4,
      risk_level: "low",
      summary: "Accelerated solar and wind capacity additions stabilize long-term price expectations and improve grid resilience.",
      model: "gemini-3.8-flash",
      tokens_used: 128,
    },
  ]);

  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([
    {
      agentName: "Business Analyst",
      role: "Requirements Engineer",
      status: "completed",
      costUsd: 0.00001,
      tokens: 140,
      summary: "Deconstructed user prompt into macro indicators and query constraints.",
      timestamp: "10:14:02",
    },
    {
      agentName: "Full-Stack Engineer",
      role: "API Integration",
      status: "completed",
      costUsd: 0.00002,
      tokens: 210,
      summary: "Invoked Vertex AI Gemini 3.8 Flash publisher endpoint via cached ADC.",
      timestamp: "10:14:04",
    },
  ]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim()) return;

    setLoading(true);
    const newStep: TraceStep = {
      agentName: "Market Analyst Agent",
      role: "Autonomous Inference",
      status: "running",
      costUsd: 0.00003,
      tokens: 180,
      summary: `Analyzing ${target} under sector ${sector}...`,
      timestamp: new Date().toLocaleTimeString(),
    };
    setTraceSteps((prev) => [newStep, ...prev]);

    try {
      const res = await fetch("/api/v1/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target, sector }),
      });
      if (res.ok) {
        const data: Report = await res.json();
        setReports((prev) => [data, ...prev]);
        setTraceSteps((prev) =>
          prev.map((s, idx) =>
            idx === 0
              ? {
                  ...s,
                  status: "completed",
                  summary: `Delivered Gemini 3.8 synthesis for ${target}.`,
                }
              : s
          )
        );
        setTarget("");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <NexusHeader
        appName="Nexus Market Pulse"
        tagline="Autonomous Economic Intelligence & Sector Synthesizer"
        activeModel="Gemini 3.8 Flash"
        budgetSpentUsd={0.00024}
        budgetCapUsd={1.0}
      />

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">System Operations & Guardrails</h2>
            <p className="text-xs text-slate-400 mt-1">Live agent telemetry and prompt shielding overview.</p>
          </div>
          <SecurityShieldBadge injectionsBlocked={3} piiScrubbed={12} />
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard title="Analyses Delivered" value={reports.length} subtitle="Cached & live reports" trend="up" trendValue="+14%" />
          <StatCard title="Average Latency" value="1.2s" subtitle="Vertex Global Endpoint" trend="neutral" trendValue="Gemini 3.8" />
          <StatCard title="Total Model Cost" value="$0.00024" subtitle="Daily budget: $1.00" trend="down" trendValue="-92% vs Claude" />
        </div>

        {/* Scan Input Form */}
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">Request Autonomous Market Scan</h3>
          <form onSubmit={handleScan} className="flex flex-col sm:flex-row gap-4">
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g. Nordic Hydrogen Pipeline, German Industrial PMI, Copper Futures..."
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
            <select
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
            >
              <option value="Macro">Macro</option>
              <option value="Energy">Energy</option>
              <option value="Technology">Technology</option>
              <option value="Commodities">Commodities</option>
            </select>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition shadow-lg shadow-indigo-600/20"
            >
              {loading ? "Synthesizing..." : "Dispatch Agent"}
            </button>
          </form>
        </section>

        {/* Grid: Reports and Telemetry */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Delivered Intelligence Reports</h3>
            {reports.map((rep) => (
              <div key={rep.id} className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-base font-semibold text-slate-100">{rep.target}</h4>
                    <span className="text-xs text-indigo-400 font-mono">{rep.sector}</span>
                  </div>
                  <AiBadge model={rep.model} status="active" />
                </div>
                <p className="text-sm leading-relaxed text-slate-300">{rep.summary}</p>
                <div className="flex items-center gap-4 text-xs font-mono text-slate-400 pt-2 border-t border-slate-800/80">
                  <span>Sentiment: {rep.sentiment_score}/100</span>
                  <span>Risk: <span className="uppercase text-emerald-400 font-bold">{rep.risk_level}</span></span>
                  <span>Tokens: {rep.tokens_used}</span>
                </div>
              </div>
            ))}
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Live Agent Activity Log</h3>
            <TraceViewer steps={traceSteps} />
          </div>
        </div>
      </main>
    </div>
  );
}
