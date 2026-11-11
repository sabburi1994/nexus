import React, { useCallback, useEffect, useState } from "react";
import { NexusHeader, type NexusNavItem } from "@nexus-agent-framework/ui";
import { OverviewSection } from "./components/OverviewSection";
import { SimulatorSection } from "./components/SimulatorSection";
import { BrownfieldSection } from "./components/BrownfieldSection";
import { TelemetrySection } from "./components/TelemetrySection";
import { DocsSection } from "./components/DocsSection";
import { PackagesSection } from "./components/PackagesSection";
import type { DocTopic, FrameworkHealth, SimulationResponse, WorkspaceTab } from "./types";

const VALID_DOC_TOPICS: readonly DocTopic[] = [
  "quickstart",
  "cli",
  "mcp",
  "orchestrators",
  "python-sdk",
  "packages",
];

function parseHashRoute(hash: string): { tab: WorkspaceTab; docTopic: DocTopic } {
  const clean = hash.replace(/^#\/?/, "").toLowerCase();
  const [head, sub] = clean.split("/");
  const docTopic = VALID_DOC_TOPICS.includes(sub as DocTopic) ? (sub as DocTopic) : "quickstart";

  if (head === "simulator" || head === "playground") return { tab: "simulator", docTopic };
  if (head === "brownfield" || head === "ast") return { tab: "brownfield", docTopic };
  if (head === "telemetry" || head === "roi" || head === "guardrails") return { tab: "telemetry", docTopic };
  if (head === "docs" || head === "documentation") return { tab: "docs", docTopic };
  if (head === "packages" || head === "registry") return { tab: "packages", docTopic };
  return { tab: "overview", docTopic };
}

export default function App() {
  const initialRoute = parseHashRoute(window.location.hash);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>(initialRoute.tab);
  const [docTopic, setDocTopic] = useState<DocTopic>(initialRoute.docTopic);
  const [health, setHealth] = useState<FrameworkHealth | null>(null);

  // Lifted session telemetry so header budget & security badges reflect live workspace activity across tabs.
  const [sessionCostUsd, setSessionCostUsd] = useState<number>(0);
  const [sessionInjectionsBlocked, setSessionInjectionsBlocked] = useState<number>(0);
  const [sessionPiiScrubbed, setSessionPiiScrubbed] = useState<number>(0);
  const [cachedSimulation, setCachedSimulation] = useState<SimulationResponse | null>(null);

  const navigate = useCallback((tab: WorkspaceTab, nextDocTopic?: DocTopic) => {
    setActiveTab(tab);
    if (nextDocTopic) {
      setDocTopic(nextDocTopic);
    }
    const targetHash = tab === "docs" && (nextDocTopic || docTopic !== "quickstart") ? `#docs/${nextDocTopic ?? docTopic}` : `#${tab}`;
    if (window.location.hash !== targetHash) {
      window.location.hash = targetHash;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [docTopic]);

  const selectDocTopic = useCallback((topic: DocTopic) => {
    setDocTopic(topic);
    const targetHash = `#docs/${topic}`;
    if (window.location.hash !== targetHash) {
      window.location.hash = targetHash;
    }
  }, []);

  const recordTelemetry = useCallback((costDeltaUsd: number, blockedDelta: number, piiDelta: number) => {
    if (costDeltaUsd > 0) setSessionCostUsd((c) => Number((c + costDeltaUsd).toFixed(6)));
    if (blockedDelta > 0) setSessionInjectionsBlocked((b) => b + blockedDelta);
    if (piiDelta > 0) setSessionPiiScrubbed((p) => p + piiDelta);
  }, []);

  useEffect(() => {
    const onHashChange = () => {
      const parsed = parseHashRoute(window.location.hash);
      setActiveTab(parsed.tab);
      if (parsed.tab === "docs") {
        setDocTopic(parsed.docTopic);
      }
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
        activeModel={cachedSimulation?.execution_mode === "byok-live" ? "gemini-3.8-flash (BYOK)" : health?.default_model ?? "gemini-3.8-flash"}
        budgetSpentUsd={sessionCostUsd}
        budgetCapUsd={1.0}
        brandHref="#overview"
        navItems={navItems}
        onNavSelect={(id) => navigate(parseHashRoute(`#${id}`).tab)}
      />

      <main className="mx-auto w-full max-w-[1260px] flex-1 px-5 py-8">
        {activeTab === "overview" && (
          <OverviewSection
            health={health}
            onNavigate={navigate}
            injectionsBlocked={sessionInjectionsBlocked}
            piiScrubbed={sessionPiiScrubbed}
          />
        )}
        {activeTab === "simulator" && (
          <SimulatorSection
            cachedResult={cachedSimulation}
            onResultChange={setCachedSimulation}
            onTelemetry={recordTelemetry}
            sessionInjectionsBlocked={sessionInjectionsBlocked}
            sessionPiiScrubbed={sessionPiiScrubbed}
          />
        )}
        {activeTab === "brownfield" && <BrownfieldSection />}
        {activeTab === "telemetry" && <TelemetrySection onTelemetry={recordTelemetry} />}
        {activeTab === "docs" && <DocsSection activeTopic={docTopic} onSelectTopic={selectDocTopic} />}
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
