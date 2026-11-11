import React from "react";
import { ExternalLink, Package } from "lucide-react";
import { DEFAULT_NEXUS_SCRAPING_POLICY } from "@nexus-agent-framework/scraper";
import { CommandBlock } from "@nexus-agent-framework/ui";
import type { FrameworkHealth } from "../types";

interface Props {
  health: FrameworkHealth | null;
}

export const PackagesSection: React.FC<Props> = ({ health }) => {
  const npmPackages = [
    {
      name: "@nexus-agent-framework/contracts",
      version: "1.0.3",
      role: "Shared Stage 0–3 TypeScript schemas & telemetry contracts",
      install: "npm install @nexus-agent-framework/contracts",
      url: "https://www.npmjs.com/package/@nexus-agent-framework/contracts",
    },
    {
      name: "@nexus-agent-framework/ui",
      version: "0.2.0",
      role: "Institutional paper-and-ink React design system & observability cards",
      install: "npm install @nexus-agent-framework/ui",
      url: "https://www.npmjs.com/package/@nexus-agent-framework/ui",
    },
    {
      name: "@nexus-agent-framework/middleware",
      version: "1.0.2",
      role: "OWASP HTTP security headers, secret scrubbing, and correlation IDs",
      install: "npm install @nexus-agent-framework/middleware",
      url: "https://www.npmjs.com/package/@nexus-agent-framework/middleware",
    },
    {
      name: "@nexus-agent-framework/scraper",
      version: "1.0.2",
      role: "Polite web scraping policies, RSS ingestion contracts, and rate limiters",
      install: "npm install @nexus-agent-framework/scraper",
      url: "https://www.npmjs.com/package/@nexus-agent-framework/scraper",
    },
  ];

  const livePypi = health?.pypi_live_version ?? "0.1.1";
  const stagedVersion = health?.pypi_staged_version ?? health?.version ?? "0.2.0";

  return (
    <div className="space-y-6">
      <section className="editorial-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e5ddd0] pb-4">
          <div>
            <p className="editorial-kicker">Published Distribution · PyPI + npm + GitHub</p>
            <h2 className="mt-1 text-2xl font-normal text-[#172a2e] sm:text-3xl">Nexus Ecosystem Packages</h2>
            <p className="mt-1 text-xs text-[#4e5b59]">
              Every package links back to <span className="font-mono">https://nexus.abburi.info</span> as its canonical
              documentation and live verification portal.
            </p>
          </div>
          <a
            href="https://github.com/sabburi1994/nexus"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded border border-[#172a2e] bg-[#172a2e] px-3.5 py-2 text-xs font-semibold text-[#fffdf8] transition hover:border-[#bd513d] hover:bg-[#bd513d]"
          >
            <span>github.com/sabburi1994/nexus</span>
            <ExternalLink size={13} />
          </a>
        </div>

        {/* Python Core Package with transparent PyPI vs main status */}
        <div className="mt-5 rounded-md border border-[#172a2e] bg-[#f8f4ec] p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-[#0f7657] px-2 py-0.5 font-mono text-[10px] font-bold uppercase text-white">
                  Python Core Runtime · v{stagedVersion} (main)
                </span>
                <span className="rounded border border-[#dfbf70] bg-[#f9edcb] px-2 py-0.5 font-mono text-[10px] font-semibold text-[#69440a]">
                  PyPI latest release: v{livePypi} · v{stagedVersion} wheel staged
                </span>
              </div>
              <h3 className="mt-2 font-mono text-lg font-semibold text-[#172a2e]">
                nexus-agent-framework == {stagedVersion}
              </h3>
              <p className="mt-1 text-xs text-[#3a494b]">
                Python 3.11+ orchestrator, 7-role IT pack, Stage 1 closed-loop self-healing, Stage 2 AST brownfield
                tooling, Stage 3 DORA ROI CLI, and 5-tool stdio MCP server. Install directly from GitHub{" "}
                <code className="font-mono">main</code> for Stage 1–3 right now, or use PyPI v{livePypi}.
              </p>
            </div>
            <a
              href="https://pypi.org/project/nexus-agent-framework/"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded border border-[#b8af9f] bg-[#fffdf8] px-3 py-1.5 font-mono text-xs font-semibold text-[#172a2e] hover:border-[#bd513d]"
            >
              <span>pypi.org</span>
              <ExternalLink size={12} />
            </a>
          </div>
          <div className="mt-4">
            <CommandBlock
              title="Python Install (Stage 1–3 from GitHub main or PyPI)"
              language="bash"
              code={`pip install "git+https://github.com/sabburi1994/nexus.git"
# PyPI registry baseline (promote wheel v0.2.0 via twine upload):
pip install nexus-agent-framework`}
            />
          </div>
        </div>

        {/* npm Packages Grid */}
        <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
          {npmPackages.map((pkg) => (
            <div key={pkg.name} className="rounded-md border border-[#d6cec0] bg-[#fffdf8] p-5">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Package size={16} className="text-[#bd513d]" />
                  <h4 className="font-mono text-sm font-semibold text-[#172a2e]">{pkg.name}</h4>
                </div>
                <span className="rounded border border-[#c9d1cf] bg-[#f1f4f2] px-2 py-0.5 font-mono text-[11px] font-semibold text-[#172a2e]">
                  v{pkg.version}
                </span>
              </div>
              <p className="mt-2 text-xs text-[#47534e]">{pkg.role}</p>
              <div className="mt-3 flex items-center justify-between border-t border-[#e5ddd0] pt-3">
                <code className="font-mono text-[11px] text-[#263aa8]">{pkg.install}</code>
                <a
                  href={pkg.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-[#bd513d] hover:underline"
                >
                  <span>npm</span>
                  <ExternalLink size={11} />
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Collapsible Live Monorepo Verification Snippet */}
      <details className="editorial-card p-5">
        <summary className="cursor-pointer font-mono text-xs font-semibold text-[#172a2e]">
          Inspect Shared Monorepo Contract Proof (@nexus-agent-framework/scraper default policy)
        </summary>
        <div className="mt-3">
          <CommandBlock
            title="Active Policy Exported by @nexus-agent-framework/scraper"
            language="json"
            code={JSON.stringify(DEFAULT_NEXUS_SCRAPING_POLICY, null, 2)}
          />
        </div>
      </details>
    </div>
  );
};
