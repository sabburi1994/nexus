import React, { useEffect, useState } from "react";
import { NexusHeader, type NexusNavItem } from "@nexus-agent-framework/ui";
import { OverviewSection } from "./components/OverviewSection";
import { SimulatorSection } from "./components/SimulatorSection";
import { BrownfieldSection } from "./components/BrownfieldSection";
import { TelemetrySection } from "./components/TelemetrySection";
import { DocsSection } from "./components/DocsSection";
import { PackagesSection } from "./components/PackagesSection";
import type { FrameworkHealth, WorkspaceTab } from "./types";

function parseHashToTab(hash: string): WorkspaceTab {
  const clean = hash.replace(/^#\/?/, "").toLowerCase();
  if (clean === "simulator" || clean === "playground") return "simulator";
  if (clean === "brownfield" || clean === "ast") return "brownfield";
  if (clean === "telemetry" || clean === "roi" || clean === "guardrails") return "telemetry";
  if (clean === "docs" || clean === "documentation") return "docs";
  if (clean === "packages" || clean === "registry") return "packages";
  return "overview";
}

export default function App() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>(() => parseHashToTab(window.location.hash));
  const [health, setHealth] = useState<FrameworkHealth | null>(null);

  const navigate = (tab: WorkspaceTab) => {
    setActiveTab(tab);
    const targetHash = `#${tab}`;
    if (window.location.hash !== targetHash) {
      window.location.hash = targetHash;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const onHashChange = () => {
      setActiveTab(parseHashToTab(window.location.hash));
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    fetch("/api/v1/framework-health")
      .then((res) => (res.ok ? res.json() : null))
      .then((data: FrameworkHealth | null) => {
        if (data) setHealth(data);
      })
      .catch(() => {
        /* fallback labels render cleanly */
      });
  }, []);

  const navItems: NexusNavItem[] = [
    { id: "overview", label: "Overview", href: "#overview", active: activeTab === "overview" },
    { id: "simulator", label: "Try Simulator", href: "#simulator", active: activeTab === "simulator", badge: "Live" },
    { id: "brownfield", label: "Brownfield AST", href: "#brownfield", active: activeTab === "brownfield" },
    { id: "telemetry", label: "ROI & Guardrails", href: "#telemetry", active: activeTab === "telemetry" },
    { id: "docs", label: "Documentation", href: "#docs", active: activeTab === "docs" },
    { id: "packages", label: "Packages", href: "#packages", active: activeTab === "packages" },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-[#f5f1e8] text-[#172a2e]">
      <NexusHeader
        appName="Nexus"
        tagline={`Agentic Engineering Framework · v${health?.version ?? "0.2.0"}`}
        activeModel={health?.default_model ?? "gemini-3.8-flash"}
        budgetSpentUsd={0.0}
        budgetCapUsd={1.0}
        brandHref="#overview"
        navItems={navItems}
        onNavSelect={(id) => navigate(parseHashToTab(`#${id}`))}
      />

      <main className="mx-auto w-full max-w-[1260px] flex-1 px-5 py-8">
        {activeTab === "overview" && <OverviewSection health={health} onNavigate={navigate} />}
        {activeTab === "simulator" && <SimulatorSection />}
        {activeTab === "brownfield" && <BrownfieldSection />}
        {activeTab === "telemetry" && <TelemetrySection />}
        {activeTab === "docs" && <DocsSection />}
        {activeTab === "packages" && <PackagesSection health={health} />}
      </main>

      <footer className="border-t border-[#c9d1cf] bg-[#fffdf8]">
        <div className="mx-auto flex max-w-[1260px] flex-wrap items-center justify-between gap-4 px-5 py-5 text-xs text-[#5c6a67]">
          <div className="flex flex-wrap items-center gap-3">
            <strong className="text-[#172a2e]">Nexus Agent Framework</strong>
            <span>·</span>
            <span>Built by Sai Nikhil Abburi</span>
            <span>·</span>
            <span className="font-mono">Apache-2.0</span>
          </div>
          <div className="flex flex-wrap items-center gap-4 font-medium">
            <a href="https://myprofile.abburi.info" target="_blank" rel="noreferrer" className="hover:text-[#bd513d]">
              myprofile.abburi.info
            </a>
            <a
              href="https://predictiveeconomics.abburi.info"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#bd513d]"
            >
              predictiveeconomics.abburi.info
            </a>
            <a
              href="https://github.com/sabburi1994/nexus"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#bd513d]"
            >
              GitHub
            </a>
            <a
              href="https://pypi.org/project/nexus-agent-framework/"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#bd513d]"
            >
              PyPI
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
