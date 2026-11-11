import React, { useState } from "react";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Cpu,
  ExternalLink,
  GitBranch,
  Layers,
  Play,
  ShieldCheck,
  Terminal,
  Wrench,
} from "lucide-react";
import { AiBadge, SecurityShieldBadge, StatCard } from "@nexus-agent-framework/ui";
import type { FrameworkHealth, WorkspaceTab } from "../types";

interface SpecialistInfo {
  id: string;
  order: string;
  name: string;
  module: string;
  outputContract: string;
  artifact: string;
  summary: string;
}

const SPECIALISTS: SpecialistInfo[] = [
  {
    id: "ba",
    order: "01",
    name: "Business Analyst",
    module: "nexus.teams.it_pack.ba.BusinessAnalystAgent",
    outputContract: "ProductProposal",
    artifact: "docs/PROPOSAL.md & preview_mockup.html",
    summary:
      "Converts rough stakeholder notes into bounded user stories, URL-safe slugs, and an interactive HTML/Tailwind preview wireframe.",
  },
  {
    id: "sa",
    order: "02",
    name: "Solution Architect",
    module: "nexus.teams.it_pack.solution_architect.SolutionArchitectAgent",
    outputContract: "SolutionBlueprint",
    artifact: "docs/ARCHITECTURE.md",
    summary:
      "Selects serverless container topologies (Cloud Run / AWS App Runner), latency targets, and Secret Manager IAM integrations.",
  },
  {
    id: "da",
    order: "03",
    name: "Data Architect",
    module: "nexus.teams.it_pack.data_architect.DataArchitectAgent",
    outputContract: "DataArchitecture",
    artifact: "docs/DATA_ARCHITECTURE.md",
    summary:
      "Defines normalized PostgreSQL 16 entities inheriting NexusEntity with UUID keys, foreign-key relations, and indexed SQL DDL.",
  },
  {
    id: "ui",
    order: "04",
    name: "UI/UX Designer",
    module: "nexus.teams.it_pack.designer.UiDesignerAgent",
    outputContract: "UiSpecification",
    artifact: "frontend/src/App.tsx",
    summary:
      "Binds institutional design tokens from @nexus-agent-framework/ui into typed React workspace components with tabular telemetry.",
  },
  {
    id: "fs",
    order: "05",
    name: "Full-Stack Engineer",
    module: "nexus.teams.it_pack.fullstack.FullStackEngineerAgent",
    outputContract: "FullStackSpecification",
    artifact: "backend/src/main.py & models.py",
    summary:
      "Implements create_nexus_app() FastAPI endpoints, Pydantic schemas, SQLAlchemy models, and type-safe frontend API clients.",
  },
  {
    id: "devops",
    order: "06",
    name: "DevOps Engineer",
    module: "nexus.teams.it_pack.devops.DevopsEngineerAgent",
    outputContract: "DevopsSpecification",
    artifact: "infra/terraform/main.tf & docker-compose.yml",
    summary:
      "Emits Cloud Run v2 Terraform modules with scale-to-zero limits, Dockerfiles, and GitHub Actions verification workflows.",
  },
  {
    id: "qa",
    order: "07",
    name: "QA & Closed-Loop Healer",
    module: "nexus.maintenance.healing_loop.ClosedLoopHealer",
    outputContract: "QaSpecification & SelfHealingReport",
    artifact: "backend/tests/test_api.py",
    summary:
      "Runs preflight security & test verification; if checks fail, dispatches exact failure diagnostics back to Full-Stack for bounded repair.",
  },
];

interface Props {
  health: FrameworkHealth | null;
  onNavigate: (tab: WorkspaceTab) => void;
}

export const OverviewSection: React.FC<Props> = ({ health, onNavigate }) => {
  const [selectedRole, setSelectedRole] = useState<string>("qa");
  const activeSpecialist = SPECIALISTS.find((s) => s.id === selectedRole) ?? SPECIALISTS[0];

  return (
    <div className="space-y-8">
      {/* Editorial Hero */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:items-stretch">
        <div className="editorial-card flex flex-col justify-between p-7 lg:col-span-8">
          <div>
            <p className="editorial-kicker">
              Orchestrator-Native Agentic Framework · v{health?.version ?? "0.2.0"}
            </p>
            <h1 className="mt-3 text-4xl font-normal leading-[1.08] tracking-tight text-[#172a2e] sm:text-5xl">
              Autonomous software squads, with{" "}
              <em className="italic text-[#bd513d]">verifiable engineering discipline.</em>
            </h1>
            <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-[#3a494b]">
              Nexus turns raw product requirements into audited FastAPI, React, SQL, and Terraform workspaces—then goes
              beyond greenfield scaffolding with <strong>Stage 1 closed-loop self-healing</strong>,{" "}
              <strong>Stage 2 AST blast-radius refactoring</strong> for legacy repositories, and{" "}
              <strong>Stage 3 DORA &amp; token ROI telemetry</strong>.
            </p>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-[#e5ddd0] pt-5">
            <button
              type="button"
              onClick={() => onNavigate("simulator")}
              className="inline-flex items-center gap-2 rounded-md border border-[#172a2e] bg-[#172a2e] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.08em] text-[#fffdf8] transition hover:border-[#bd513d] hover:bg-[#bd513d]"
            >
              <Play size={14} />
              <span>Try Live Simulator</span>
            </button>
            <button
              type="button"
              onClick={() => onNavigate("brownfield")}
              className="inline-flex items-center gap-2 rounded-md border border-[#b8af9f] bg-[#f8f4ec] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.08em] text-[#172a2e] transition hover:border-[#172a2e] hover:bg-[#efe8da]"
            >
              <GitBranch size={14} />
              <span>Run AST Blast-Radius</span>
            </button>
            <button
              type="button"
              onClick={() => onNavigate("docs")}
              className="inline-flex items-center gap-1.5 px-2 py-2 text-xs font-semibold text-[#3a494b] underline underline-offset-4 transition hover:text-[#bd513d]"
            >
              <BookOpen size={14} />
              <span>Documentation &amp; MCP Setup</span>
            </button>
          </div>
        </div>

        {/* Live Verification Ledger */}
        <aside className="editorial-card flex flex-col justify-between bg-[#f8f4ec] p-6 lg:col-span-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#d6cec0] pb-3">
              <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#172a2e]">
                Runtime Ledger
              </span>
              <AiBadge model={health?.default_model ?? "gemini-3.8-flash"} status="active" />
            </div>

            <dl className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between border-b border-[#e5ddd0] pb-2">
                <dt className="text-[#5c6a67]">Core Pytest Gate</dt>
                <dd className="tabular-mono font-semibold text-[#0f7657]">
                  {health ? `${health.tests_passed}/${health.tests_total} PASS` : "30/30 PASS"}
                </dd>
              </div>
              <div className="flex items-center justify-between border-b border-[#e5ddd0] pb-2">
                <dt className="text-[#5c6a67]">Gemini 3.8 Input</dt>
                <dd className="tabular-mono font-medium text-[#172a2e]">
                  {health?.pricing_model?.gemini_3_8_flash_input_per_m ?? "$0.075 / 1M"}
                </dd>
              </div>
              <div className="flex items-center justify-between border-b border-[#e5ddd0] pb-2">
                <dt className="text-[#5c6a67]">Local Mock Mode</dt>
                <dd className="tabular-mono font-medium text-[#0f7657]">$0.0000 (Offline CI)</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-[#5c6a67]">MCP Transport</dt>
                <dd className="tabular-mono font-medium text-[#172a2e]">JSON-RPC 2.0 (stdio)</dd>
              </div>
            </dl>
          </div>

          <div className="mt-5 space-y-3 border-t border-[#d6cec0] pt-4">
            <SecurityShieldBadge injectionsBlocked={0} piiScrubbed={0} />
            <p className="text-[11px] leading-relaxed text-[#5c6a67]">
              Every prompt passes through{" "}
              <code className="rounded border border-[#d6cec0] bg-[#fffdf8] px-1 py-0.5 font-mono text-[10px]">
                GuardrailManager
              </code>{" "}
              before entering model execution.
            </p>
          </div>
        </aside>
      </section>

      {/* KPI Strip rendered directly via @nexus-agent-framework/ui StatCard */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Virtual IT Squad"
          value="7 Roles"
          subtitle="BA → Architect → Data → UI → Dev → Ops → QA"
          accent="default"
        />
        <StatCard
          title="Stage 1 Self-Healing"
          value="<= 3 Cycles"
          subtitle="Bounded QA failure diagnosis & repair"
          trend="up"
          trendValue="Closed-Loop"
          accent="terracotta"
        />
        <StatCard
          title="Stage 2 Brownfield"
          value="AST Graph"
          subtitle="Imports, routes, tests & secret audit"
          trend="up"
          trendValue="Zero-Blind-Edit"
          accent="cobalt"
        />
        <StatCard
          title="Stage 3 Telemetry"
          value="DORA + ROI"
          subtitle="Benchmarks token spend vs engineering hours"
          trend="up"
          trendValue="CLI + JSON"
          accent="emerald"
        />
      </section>

      {/* Interactive 7-Specialist Squad Topology */}
      <section className="editorial-card p-6">
        <div className="flex flex-wrap items-end justify-between gap-4 border-b border-[#e5ddd0] pb-4">
          <div>
            <p className="editorial-kicker">Architecture Anatomy</p>
            <h2 className="mt-1 text-2xl font-normal text-[#172a2e]">
              Inside <span className="font-mono text-xl">NexusITTeam.build_from_idea()</span>
            </h2>
          </div>
          <button
            type="button"
            onClick={() => onNavigate("simulator")}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#bd513d] hover:underline"
          >
            <span>Execute live pipeline in Simulator</span>
            <ArrowRight size={13} />
          </button>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-2.5 sm:grid-cols-4 lg:grid-cols-7">
          {SPECIALISTS.map((role) => {
            const active = role.id === activeSpecialist.id;
            return (
              <button
                key={role.id}
                type="button"
                onClick={() => setSelectedRole(role.id)}
                className={`rounded-md border p-3 text-left transition ${
                  active
                    ? "border-[#172a2e] bg-[#172a2e] text-[#fffdf8] shadow-[3px_3px_0_#bd513d]"
                    : "border-[#d6cec0] bg-[#f8f4ec] text-[#172a2e] hover:border-[#bd513d]"
                }`}
              >
                <p className={`tabular-mono text-[10px] font-bold ${active ? "text-[#efdca2]" : "text-[#bd513d]"}`}>
                  STEP {role.order}
                </p>
                <p className="mt-1 text-xs font-semibold leading-snug">{role.name}</p>
              </button>
            );
          })}
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 rounded-md border border-[#d6cec0] bg-[#f8f4ec] p-5 md:grid-cols-3">
          <div className="md:col-span-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-[#172a2e] px-2 py-0.5 font-mono text-[11px] font-semibold text-[#fffdf8]">
                Stage {activeSpecialist.order}
              </span>
              <h3 className="text-base font-semibold text-[#172a2e]">{activeSpecialist.name}</h3>
            </div>
            <p className="mt-2.5 text-sm leading-relaxed text-[#3a494b]">{activeSpecialist.summary}</p>
            <p className="mt-3 font-mono text-xs text-[#5c6a67]">
              Class: <span className="text-[#172a2e]">{activeSpecialist.module}</span>
            </p>
          </div>
          <div className="flex flex-col justify-between rounded border border-[#d6cec0] bg-[#fffdf8] p-4 text-xs">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-[#5c6a67]">Pydantic Schema Contract</p>
              <p className="mt-1 font-mono font-semibold text-[#263aa8]">{activeSpecialist.outputContract}</p>
              <p className="mt-3 text-[10px] font-bold uppercase tracking-wider text-[#5c6a67]">Emitted Disk Artifact</p>
              <p className="mt-1 font-mono text-[#0f7657]">{activeSpecialist.artifact}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Three Stage Deep-Link Cards + Engineering Honesty */}
      <section className="grid grid-cols-1 gap-5 md:grid-cols-3">
        <article className="editorial-card flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center gap-2 text-[#bd513d]">
              <Wrench size={16} />
              <span className="text-[11px] font-bold uppercase tracking-[0.11em]">Stage 1 · Reliability</span>
            </div>
            <h3 className="mt-2 text-lg font-semibold text-[#172a2e]">Closed-Loop Self-Healing</h3>
            <p className="mt-2 text-xs leading-relaxed text-[#47534e]">
              Instead of dumping unverified files on disk, QA evaluates preflight checks and feeds failures into{" "}
              <code className="font-mono">ClosedLoopHealer</code>, capping repair loops at{" "}
              <code className="font-mono">max_healing_cycles</code> so runaway retries never blow token budgets.
            </p>
          </div>
          <button
            type="button"
            onClick={() => onNavigate("simulator")}
            className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-[#172a2e] hover:text-[#bd513d]"
          >
            <span>Watch healing in Simulator</span>
            <ArrowRight size={13} />
          </button>
        </article>

        <article className="editorial-card flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center gap-2 text-[#263aa8]">
              <Layers size={16} />
              <span className="text-[11px] font-bold uppercase tracking-[0.11em]">Stage 2 · Existing Repos</span>
            </div>
            <h3 className="mt-2 text-lg font-semibold text-[#172a2e]">AST Blast-Radius Refactoring</h3>
            <p className="mt-2 text-xs leading-relaxed text-[#47534e]">
              Before editing a legacy module, <code className="font-mono">AstDependencyMapper</code> parses imports,
              classes, and FastAPI routes to surface direct dependents, indirect blast radius, exposed keys, and exact
              affected test suites.
            </p>
          </div>
          <button
            type="button"
            onClick={() => onNavigate("brownfield")}
            className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-[#172a2e] hover:text-[#263aa8]"
          >
            <span>Inspect sample codebase AST</span>
            <ArrowRight size={13} />
          </button>
        </article>

        <article className="editorial-card flex flex-col justify-between p-6">
          <div>
            <div className="flex items-center gap-2 text-[#0f7657]">
              <Activity size={16} />
              <span className="text-[11px] font-bold uppercase tracking-[0.11em]">Stage 3 · Accountability</span>
            </div>
            <h3 className="mt-2 text-lg font-semibold text-[#172a2e]">DORA Metrics &amp; Guardrail Audit</h3>
            <p className="mt-2 text-xs leading-relaxed text-[#47534e]">
              <code className="font-mono">RoiCalculator</code> quantifies real token spend against engineering hours,
              while <code className="font-mono">GuardrailManager</code> and{" "}
              <code className="font-mono">@nexus-agent-framework/middleware</code> block prompt injections and redact
              leaked credentials.
            </p>
          </div>
          <button
            type="button"
            onClick={() => onNavigate("telemetry")}
            className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-[#172a2e] hover:text-[#0f7657]"
          >
            <span>Open ROI &amp; Guardrail sandbox</span>
            <ArrowRight size={13} />
          </button>
        </article>
      </section>

      {/* Honest Boundaries & Sister abburi.info Ecosystem */}
      <section className="editorial-card grid grid-cols-1 gap-6 bg-[#f8f4ec] p-6 lg:grid-cols-2">
        <div>
          <div className="flex items-center gap-2 text-[#172a2e]">
            <ShieldCheck size={16} className="text-[#0f7657]" />
            <h3 className="text-sm font-bold uppercase tracking-wider">Engineering Boundaries (What Nexus Does Not Hide)</h3>
          </div>
          <ul className="mt-3 space-y-2 text-xs leading-relaxed text-[#3a494b]">
            <li>
              <strong>Provider reality:</strong> Live LLM synthesis requires Google Vertex AI ADC or{" "}
              <code className="font-mono">GEMINI_API_KEY</code>. This public portal runs the real Python squad engine
              with deterministic offline synthesis so anonymous visitors never hit credential blocks or bill surprises.
            </li>
            <li>
              <strong>Human architecture ownership:</strong> Nexus drafts FastAPI routes, Pydantic contracts, Terraform
              skeletons, and diffs cleanly—humans review blasts and hold final production merge keys.
            </li>
          </ul>
        </div>
        <div className="flex flex-col justify-between border-t border-[#d6cec0] pt-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          <div>
            <div className="flex items-center gap-2 text-[#172a2e]">
              <Cpu size={16} className="text-[#bd513d]" />
              <h3 className="text-sm font-bold uppercase tracking-wider">Part of the abburi.info Platform</h3>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#47534e]">
              Built with the same editorial paper components, tabular numeric discipline, and Cloud Run architecture used
              across my engineering portfolio and public AI research applications.
            </p>
          </div>
          <div className="mt-4 flex flex-wrap gap-3 text-xs font-semibold">
            <a
              href="https://myprofile.abburi.info"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded border border-[#c9d1cf] bg-[#fffdf8] px-3 py-1.5 text-[#172a2e] hover:border-[#bd513d] hover:text-[#bd513d]"
            >
              <span>myprofile.abburi.info</span>
              <ExternalLink size={12} />
            </a>
            <a
              href="https://predictiveeconomics.abburi.info"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded border border-[#c9d1cf] bg-[#fffdf8] px-3 py-1.5 text-[#172a2e] hover:border-[#263aa8] hover:text-[#263aa8]"
            >
              <span>predictiveeconomics.abburi.info</span>
              <ExternalLink size={12} />
            </a>
            <button
              type="button"
              onClick={() => onNavigate("packages")}
              className="inline-flex items-center gap-1 rounded border border-[#c9d1cf] bg-[#fffdf8] px-3 py-1.5 text-[#172a2e] hover:border-[#0f7657]"
            >
              <Terminal size={12} />
              <span>PyPI &amp; npm Registry</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
