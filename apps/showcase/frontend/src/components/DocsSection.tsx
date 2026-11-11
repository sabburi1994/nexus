import React, { useState } from "react";
import { BookOpen, Cpu, Terminal, Wrench } from "lucide-react";
import { CommandBlock } from "@nexus-agent-framework/ui";

type DocTopic = "quickstart" | "cli" | "mcp" | "python-sdk" | "packages";

const TOPICS: Array<{ id: DocTopic; title: string; subtitle: string }> = [
  { id: "quickstart", title: "1. Quickstart & Install", subtitle: "PyPI, npm, and offline MockProvider" },
  { id: "cli", title: "2. CLI Reference", subtitle: "doctor, dream, ui, audit, refactor, metrics" },
  { id: "mcp", title: "3. MCP Integration", subtitle: "Claude Code, Cursor, Codex & Gemini" },
  { id: "python-sdk", title: "4. Python Core SDK", subtitle: "create_nexus_app, GuardrailManager, Healer" },
  { id: "packages", title: "5. TypeScript Contracts", subtitle: "@nexus-agent-framework/* monorepo" },
];

export const DocsSection: React.FC = () => {
  const [topic, setTopic] = useState<DocTopic>("quickstart");

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      {/* Sidebar Index */}
      <aside className="lg:col-span-4">
        <div className="editorial-card sticky top-24 p-5">
          <div className="flex items-center gap-2 border-b border-[#e5ddd0] pb-3">
            <BookOpen size={15} className="text-[#bd513d]" />
            <h2 className="text-sm font-semibold text-[#172a2e]">Engineering Documentation</h2>
          </div>
          <nav aria-label="Documentation topics" className="mt-3 space-y-1.5">
            {TOPICS.map((item) => {
              const active = topic === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setTopic(item.id)}
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
        {topic === "quickstart" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Getting Started · Python 3.11+ &amp; Node 18+</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">Installation &amp; Zero-Cost Verification</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3a494b]">
                Install the core Python runtime from PyPI alongside the shared TypeScript contracts and React UI
                primitives from npm. You can verify the entire 7-agent pipeline offline using{" "}
                <code className="font-mono">MockProvider</code> or connect Google Vertex AI for live Gemini 3.8
                synthesis.
              </p>
            </div>

            <CommandBlock
              title="Install Core Framework & Verify Environment"
              language="bash"
              code={`pip install nexus-agent-framework
nexus --version
nexus doctor`}
            />

            <CommandBlock
              title="Install Shared Monorepo TypeScript Packages"
              language="bash"
              code={`npm install @nexus-agent-framework/contracts @nexus-agent-framework/ui @nexus-agent-framework/middleware`}
            />

            <div className="rounded border border-[#d6cec0] bg-[#f8f4ec] p-4 text-xs leading-relaxed text-[#3a494b]">
              <p className="font-semibold text-[#172a2e]">Vertex AI vs Gemini API Key Configuration</p>
              <p className="mt-1">
                Authenticate via Google Cloud Application Default Credentials (<code className="font-mono">gcloud auth application-default login</code>) with <code className="font-mono">GCP_PROJECT_ID</code>, or export <code className="font-mono">GEMINI_API_KEY</code>. Pricing defaults track <code className="font-mono">gemini-3.8-flash</code>.
              </p>
            </div>
          </>
        )}

        {topic === "cli" && (
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
              code={`nexus metrics ./existing-service --hourly-rate 95`}
            />
          </>
        )}

        {topic === "mcp" && (
          <>
            <div className="border-b border-[#e5ddd0] pb-4">
              <p className="editorial-kicker">Model Context Protocol · Orchestrator-Native</p>
              <h2 className="mt-1 text-3xl font-normal text-[#172a2e]">Connect Claude Code, Cursor &amp; Codex</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#3a494b]">
                Instead of replacing your primary coding IDE agent, <code className="font-mono">nexus mcp</code> exposes
                Nexus tools over standard JSON-RPC 2.0 stdio transport so orchestrators can invoke guarded execution and
                AST checks natively.
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

            <CommandBlock
              title="Launch MCP Server Directly"
              language="bash"
              code={`nexus mcp`}
            />
          </>
        )}

        {topic === "python-sdk" && (
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

        {topic === "packages" && (
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
