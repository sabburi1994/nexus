import React from "react";
import { BookOpen, Cpu, Link2, Terminal, Wrench } from "lucide-react";
import { CommandBlock } from "@nexus-agent-framework/ui";
import type { DocTopic } from "../types";

const TOPICS: Array<{ id: DocTopic; title: string; subtitle: string }> = [
  { id: "quickstart", title: "1. Quickstart & Install", subtitle: "PyPI, npm, and offline MockProvider" },
  { id: "cli", title: "2. CLI Reference", subtitle: "doctor, dream, ui, audit, refactor, metrics" },
  { id: "mcp", title: "3. MCP Integration", subtitle: "5 stdio tools for IDEs & orchestrators" },
  { id: "orchestrators", title: "4. Orchestrator Fit", subtitle: "Plugging into zeroshot, Claude Code, Codex" },
  { id: "python-sdk", title: "5. Python Core SDK", subtitle: "create_nexus_app, GuardrailManager, Healer" },
  { id: "packages", title: "6. TypeScript Contracts", subtitle: "@nexus-agent-framework/* monorepo" },
];

const MCP_TOOLS = [
  {
    name: "nexus_check_ai",
    params: 'model: str = "gemini-3.8-flash"',
    returns: "Vertex AI / Gemini connectivity & response status",
  },
  {
    name: "nexus_audit",
    params: 'path: str = "."',
    returns: "CodebaseAuditor findings (SECRET_LEAK, MISSING_GUARDRAIL, score/100)",
  },
  {
    name: "nexus_blast_radius",
    params: 'target: str, path: str = "."',
    returns: "AstDependencyMapper direct/indirect dependents, affected routes & tests",
  },
  {
    name: "nexus_guardrail",
    params: "text: str",
    returns: "Prompt injection verdict + credential/email redacted text",
  },
  {
    name: "nexus_roi",
    params: 'path: str = ".", hourly_rate: float = 85.0',
    returns: "EnterpriseRoiReport with token spend vs engineering hours & DORA metrics",
  },
];

interface Props {
  activeTopic: DocTopic;
  onSelectTopic: (topic: DocTopic) => void;
}

export const DocsSection: React.FC<Props> = ({ activeTopic, onSelectTopic }) => {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      {/* Sidebar Index */}
      <aside className="lg:col-span-4">
        <div className="editorial-card sticky top-24 p-5">
          <div className="flex items-center justify-between border-b border-[#e5ddd0] pb-3">
            <div className="flex items-center gap-2">
              <BookOpen size={15} className="text-[#bd513d]" />
              <h2 className="text-sm font-semibold text-[#172a2e]">Engineering Documentation</h2>
            </div>
            <span className="inline-flex items-center gap-1 font-mono text-[10px] text-[#5c6a67]">
              <Link2 size={10} /> #{`docs/${activeTopic}`}
            </span>
          </div>
          <nav aria-label="Documentation topics" className="mt-3 space-y-1.5">
            {TOPICS.map((item) => {
              const active = activeTopic === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectTopic(item.id)}
                  className={`w-full rounded border px-3 py-2.5 text-left transition ${
                    active
                      ? "border-[#172a2e] bg-[#172a2e] text-[#fffdf8]"
                      : "border-[#d6cec0] bg-[#f8f4ec] text-[#172a2e] hover:border-[#bd513d]"
                  }`}
                >
                  <p className="text-xs font-semibold">{item.title}</p>
                  <p className={`text-[11px] ${active ? "text-[#d4e0de]" : "text-[#5c6a67]"}`}>{item.subtitle}</p>
                </button>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Main Article */}
      <article className="editorial-card space-y-6 p-7 lg:col-span-8">
        {activeTopic === "quickstart" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Getting Started · Python 3.11+ &amp; Node 18+</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">Installation &amp; Zero-Cost Verification</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3a494b]">
                Install the core Python runtime alongside the published TypeScript contracts and React UI primitives from
                npm. Verify the entire 7-agent pipeline offline using <code className="font-mono">MockProvider</code> or
                connect Google Vertex AI / Gemini API keys for live Gemini 3.8 synthesis.
              </p>
            </div>

            <CommandBlock
              title="Install Core Framework & Verify Environment (v0.2.0 Stage 1–3 on main)"
              language="bash"
              code={`pip install "git+https://github.com/sabburi1994/nexus.git"
# Or from PyPI once v0.2.0 is promoted (latest PyPI baseline: 0.1.1):
pip install nexus-agent-framework
nexus --version
nexus doctor`}
            />

            <CommandBlock
              title="Install Shared Monorepo TypeScript Packages (Published Live on npm)"
              language="bash"
              code={`npm install @nexus-agent-framework/contracts @nexus-agent-framework/ui @nexus-agent-framework/middleware`}
            />

            <div className="rounded border border-[#d6cec0] bg-[#f8f4ec] p-4 text-xs leading-relaxed text-[#3a494b]">
              <p className="font-semibold text-[#172a2e]">Vertex AI vs Gemini API Key Precedence</p>
              <p className="mt-1">
                Passing an explicit <code className="font-mono">GeminiClient(api_key=...)</code> uses direct Gemini REST
                endpoints; otherwise <code className="font-mono">GeminiClient</code> authenticates via Google Cloud ADC (
                <code className="font-mono">gcloud auth application-default login</code>) or{" "}
                <code className="font-mono">GEMINI_API_KEY</code>.
              </p>
            </div>
          </>
        )}

        {activeTopic === "cli" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Command Line Interface · src/nexus/cli/main.py</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">CLI Workflows Across Stages 1–3</h2>
            </div>

            <CommandBlock
              title="Stage 0 + 1: Generate Full-Stack App with Closed-Loop Healing"
              language="bash"
              code={`nexus dream "European invoice dispute triage service" --output-dir ./workspace
nexus ui --port 8000`}
            />

            <CommandBlock
              title="Stage 2: Audit Legacy Repos & Compute AST Blast Radius"
              language="bash"
              code={`nexus audit ./existing-service --json
nexus refactor "Move legacy API key to env var and wrap LLM call" --target src/models.py --apply`}
            />

            <CommandBlock
              title="Stage 3: Generate Enterprise ROI & DORA Terminal Scorecard"
              language="bash"
              code={`nexus metrics ./existing-service --hourly-rate 95 --json`}
            />
          </>
        )}

        {activeTopic === "mcp" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Model Context Protocol · src/nexus/orchestrator/mcp.py</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">Stdio MCP Server (5 Stage 1–3 Tools)</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3a494b]">
                <code className="font-mono">nexus mcp</code> starts a JSON-RPC 2.0 stdio server exposing read-only
                guardrail, audit, blast-radius, ROI, and connectivity tools so external orchestrators inspect repos
                safely before writing diffs.
              </p>
            </div>

            <CommandBlock
              title=".cursor/mcp.json or claude_desktop_config.json"
              language="json"
              code={`{
  "mcpServers": {
    "nexus": {
      "command": "nexus",
      "args": ["mcp"],
      "env": {
        "GCP_PROJECT_ID": "your-gcp-project-id"
      }
    }
  }
}`}
            />

            <div className="overflow-x-auto rounded border border-[#d6cec0]">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#d6cec0] bg-[#f8f4ec] font-mono text-[11px] uppercase text-[#5c6a67]">
                  <tr>
                    <th className="px-3.5 py-2.5">MCP Tool Name</th>
                    <th className="px-3.5 py-2.5">Parameters</th>
                    <th className="px-3.5 py-2.5">Output / Responsibility</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e5ddd0] bg-[#fffdf8]">
                  {MCP_TOOLS.map((tool) => (
                    <tr key={tool.name}>
                      <td className="px-3.5 py-2.5 font-mono font-semibold text-[#bd513d]">{tool.name}</td>
                      <td className="px-3.5 py-2.5 font-mono text-[11px] text-[#263aa8]">{tool.params}</td>
                      <td className="px-3.5 py-2.5 text-[#3a494b]">{tool.returns}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {activeTopic === "orchestrators" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Ecosystem Architecture · Orchestrator-Native</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">
                Using Nexus Alongside zeroshot, Claude Code &amp; Codex
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3a494b]">
                Nexus intentionally avoids locking teams into a single IDE harness. Your primary coding orchestrator
                calls Nexus primitives over <code className="font-mono">nexus mcp</code> or Python APIs as deterministic
                pre-flight and post-edit verification gates.
              </p>
            </div>

            <div className="overflow-x-auto rounded border border-[#d6cec0] bg-[#f8f4ec] p-4">
              <svg viewBox="0 0 680 120" className="h-auto w-full min-w-[520px]" role="img" aria-label="Orchestrator Flow">
                {[
                  { x: 10, title: "1. External Prompt", sub: "IDE / zeroshot", fill: "#fffdf8", stroke: "#c9d1cf", text: "#172a2e" },
                  { x: 180, title: "2. GuardrailManager", sub: "nexus_guardrail", fill: "#fbece7", stroke: "#bd513d", text: "#7f2419" },
                  { x: 350, title: "3. AST Scope Gate", sub: "nexus_blast_radius", fill: "#eef1fb", stroke: "#263aa8", text: "#263aa8" },
                  { x: 520, title: "4. ClosedLoopHealer", sub: "Audit + Retry <= 3x", fill: "#e6f4ee", stroke: "#0f7657", text: "#0f7657" },
                ].map((b, i) => (
                  <g key={b.title}>
                    <rect x={b.x} y={24} width={150} height={68} rx={6} fill={b.fill} stroke={b.stroke} strokeWidth={1.6} />
                    <text
                      x={b.x + 75}
                      y={52}
                      textAnchor="middle"
                      fill={b.text}
                      style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontSize: "11px", fontWeight: 700 }}
                    >
                      {b.title}
                    </text>
                    <text
                      x={b.x + 75}
                      y={72}
                      textAnchor="middle"
                      fill={b.text}
                      style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px" }}
                    >
                      {b.sub}
                    </text>
                    {i < 3 && (
                      <line x1={b.x + 150} y1={58} x2={b.x + 178} y2={58} stroke="#5c6a67" strokeWidth={2} />
                    )}
                  </g>
                ))}
              </svg>
            </div>

            <CommandBlock
              title="Typical Pre-Edit + Post-Edit Gate Loop in an Autonomous Graph"
              language="bash"
              code={`# 1. Before any worker modifies core modules: check dependents & test suites
nexus audit ./service --json
nexus refactor "Externalize token" --target config.py

# 2. After worker applies edits: compute DORA & security clearance delta
nexus audit ./service
nexus metrics ./service --hourly-rate 95`}
            />
          </>
        )}

        {activeTopic === "python-sdk" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Python SDK · FastAPI + Guardrails + Self-Healing</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">Building Services with Nexus Core</h2>
            </div>

            <CommandBlock
              title="Production Microservice with create_nexus_app + GuardrailManager"
              language="python"
              code={`from fastapi import HTTPException
from nexus.api import create_nexus_app
from nexus.ai import GeminiClient
from nexus.security import GuardrailManager, SecurityViolationError

app, db = create_nexus_app(title="Treasury Triage API", version="1.0.0")
guard = GuardrailManager()
client = GeminiClient(default_model="gemini-3.8-flash")

@app.post("/api/v1/triage")
async def triage(prompt: str) -> dict[str, str]:
    try:
        clean = guard.inspect_input(prompt)
    except SecurityViolationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    reply = client.generate(clean)
    return {"answer": reply.text, "model": reply.model}`}
            />

            <CommandBlock
              title="Programmatic Stage 2 AST Analysis & Stage 3 ROI"
              language="python"
              code={`from nexus.brownfield import AstDependencyMapper, CodebaseAuditor
from nexus.metrics.roi import RoiCalculator

audit = CodebaseAuditor("./repo").run_audit()
mapper = AstDependencyMapper("./repo")
mapper.scan_codebase()
blast = mapper.compute_blast_radius("models.py")
roi = RoiCalculator(hourly_rate=95.0).calculate_from_codebase("./repo")`}
            />
          </>
        )}

        {activeTopic === "packages" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">TypeScript &amp; React Monorepo Packages</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">How This Website Consumes Nexus Packages</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3a494b]">
                This documentation site (<code className="font-mono">apps/showcase/frontend</code>) is itself a consumer
                of <code className="font-mono">@nexus-agent-framework/ui</code>,{" "}
                <code className="font-mono">contracts</code>, <code className="font-mono">middleware</code>, and{" "}
                <code className="font-mono">scraper</code>, sharing strict interfaces with the Python FastAPI backend.
              </p>
            </div>

            <CommandBlock
              title="TypeScript Usage Example (Same Components Powering nexus.abburi.info)"
              language="tsx"
              code={`import type { BlastRadiusContract, EnterpriseRoiContract } from "@nexus-agent-framework/contracts";
import { scrubSensitiveData, generateCorrelationId } from "@nexus-agent-framework/middleware";
import { NexusHeader, BlastRadiusCard, RoiScorecard, HealingLoopPanel } from "@nexus-agent-framework/ui";

const safePrompt = scrubSensitiveData(rawInput);
const cid = generateCorrelationId();`}
            />

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded border border-[#d6cec0] bg-[#f8f4ec] p-3 text-xs">
                <Cpu size={14} className="text-[#bd513d]" />
                <p className="mt-1 font-semibold text-[#172a2e]">Strict TypeScript</p>
                <p className="mt-0.5 text-[#5c6a67]">Compiled via tsc -p across all 4 packages in CI.</p>
              </div>
              <div className="rounded border border-[#d6cec0] bg-[#f8f4ec] p-3 text-xs">
                <Wrench size={14} className="text-[#263aa8]" />
                <p className="mt-1 font-semibold text-[#172a2e]">Ruff + Mypy Strict</p>
                <p className="mt-0.5 text-[#5c6a67]">Zero-warning Python type checks across src/ and tests/.</p>
              </div>
              <div className="rounded border border-[#d6cec0] bg-[#f8f4ec] p-3 text-xs">
                <Terminal size={14} className="text-[#0f7657]" />
                <p className="mt-1 font-semibold text-[#172a2e]">Cloud Run Container</p>
                <p className="mt-0.5 text-[#5c6a67]">Vite bundle + wheel deployed cleanly on finhub-510316.</p>
              </div>
            </div>
          </>
        )}
      </article>
    </div>
  );
};
