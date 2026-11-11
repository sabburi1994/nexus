import React, { useEffect, useState } from "react";
import { AlertOctagon, CheckCircle2, FileCode2, GitFork, RefreshCw, ShieldAlert, Wand2 } from "lucide-react";
import { BlastRadiusCard, CommandBlock, StatCard } from "@nexus-agent-framework/ui";
import { AstDependencyGraph } from "./AstDependencyGraph";
import type { BrownfieldApplyPreviewResponse, BrownfieldInspectResponse } from "../types";

const CUSTOM_INSECURE_TEMPLATE: Record<string, string> = {
  "config.py": `LEGACY_TOKEN = "sk-demo9876543210abcdef9876543210"\nMODEL = "gemini-3.8-flash"\n`,
  "models.py": `from pydantic import BaseModel\n\nclass Order(BaseModel):\n    order_id: str\n    amount: float\n`,
  "service.py": `from models import Order\nfrom nexus.ai import GeminiClient\n\ndef summarize(order: Order, user_text: str) -> str:\n    client = GeminiClient()\n    return client.generate(f"Summarize {order.order_id}: {user_text}").text\n`,
  "api.py": `from fastapi import FastAPI\nfrom models import Order\nfrom service import summarize\n\napp = FastAPI()\n\n@app.post("/api/v1/orders/summary")\ndef order_summary(order: Order, note: str):\n    return {"summary": summarize(order, note)}\n`,
  "tests/test_api.py": `import api\n\ndef test_routes():\n    assert api.app is not None\n`,
};

const CUSTOM_GUARDED_TEMPLATE: Record<string, string> = {
  "config.py": `import os\n\nLEGACY_TOKEN = os.getenv("LEGACY_TOKEN", "")\nMODEL = "gemini-3.8-flash"\n`,
  "models.py": CUSTOM_INSECURE_TEMPLATE["models.py"],
  "service.py": `from models import Order\nfrom nexus.ai import GeminiClient\nfrom nexus.security import GuardrailManager\n\n_guardrail = GuardrailManager()\n\ndef summarize(order: Order, user_text: str) -> str:\n    safe_text = _guardrail.inspect_input(user_text)\n    client = GeminiClient()\n    return client.generate(f"Summarize {order.order_id}: {safe_text}").text\n`,
  "api.py": CUSTOM_INSECURE_TEMPLATE["api.py"],
  "tests/test_api.py": CUSTOM_INSECURE_TEMPLATE["tests/test_api.py"],
};

export const BrownfieldSection: React.FC = () => {
  const [sourceMode, setSourceMode] = useState<"sample" | "custom">("sample");
  const [targetFile, setTargetFile] = useState<string>("models.py");
  const [refactorTask, setRefactorTask] = useState<string>(
    "Wrap unguarded GeminiClient calls with GuardrailManager and externalize legacy tokens"
  );
  const [customFiles, setCustomFiles] = useState<Record<string, string>>(CUSTOM_INSECURE_TEMPLATE);
  const [activeFile, setActiveFile] = useState<string>("models.py");
  const [data, setData] = useState<BrownfieldInspectResponse | null>(null);
  const [applyPreview, setApplyPreview] = useState<BrownfieldApplyPreviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [applying, setApplying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runInspect = async (
    overrideTarget?: string,
    overrideMode?: "sample" | "custom",
    overrideCustomFiles?: Record<string, string>
  ) => {
    const mode = overrideMode ?? sourceMode;
    const tgt = overrideTarget ?? targetFile;
    const filesPayload = overrideCustomFiles ?? customFiles;
    setLoading(true);
    setError(null);
    setApplyPreview(null);
    try {
      const res = await fetch("/api/v1/brownfield/inspect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_mode: mode,
          target_file: tgt,
          refactor_task: refactorTask,
          custom_files: mode === "custom" ? filesPayload : undefined,
        }),
      });
      const json = await res.json();
      if (!res.ok) {
        setError(json.detail || "Brownfield AST scan failed.");
      } else {
        setData(json as BrownfieldInspectResponse);
        setTargetFile(json.selectedTarget);
        if (!json.files[activeFile]) {
          setActiveFile(json.selectedTarget);
        }
      }
    } catch {
      setError("Could not reach backend AST analyzer.");
    } finally {
      setLoading(false);
    }
  };

  const runApplyPreview = async () => {
    setApplying(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/brownfield/apply-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_mode: sourceMode,
          target_file: targetFile,
          refactor_task: refactorTask,
          custom_files: sourceMode === "custom" ? customFiles : undefined,
        }),
      });
      const json = await res.json();
      if (!res.ok) {
        setError(json.detail || "Failed to simulate remediation patches.");
      } else {
        setApplyPreview(json as BrownfieldApplyPreviewResponse);
      }
    } catch {
      setError("Could not reach backend patch simulator.");
    } finally {
      setApplying(false);
    }
  };

  useEffect(() => {
    void runInspect("models.py", "sample");
  }, []);

  const fileList = Object.keys(sourceMode === "custom" ? customFiles : data?.files ?? {});

  return (
    <div className="space-y-6">
      <section className="editorial-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e5ddd0] pb-4">
          <div>
            <p className="editorial-kicker">Stage 2 · Python ast + CodebaseAuditor + BrownfieldRefactorer</p>
            <h2 className="mt-1 text-2xl font-normal text-[#172a2e] sm:text-3xl">
              Brownfield AST Blast-Radius &amp; Security Auditor
            </h2>
            <p className="mt-1 text-xs text-[#4e5b59]">
              Parses real Python AST imports, FastAPI route decorators, and security anti-patterns across existing
              repositories before proposing surgical diffs.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setSourceMode("sample");
                setTargetFile("models.py");
                void runInspect("models.py", "sample");
              }}
              className={`rounded px-3 py-1.5 text-xs font-semibold transition ${
                sourceMode === "sample"
                  ? "bg-[#172a2e] text-[#fffdf8]"
                  : "border border-[#c9d1cf] bg-[#f8f4ec] text-[#3a494b]"
              }`}
            >
              Bundled Legacy Billing Repo
            </button>
            <button
              type="button"
              onClick={() => {
                setSourceMode("custom");
                setCustomFiles(CUSTOM_INSECURE_TEMPLATE);
                setTargetFile("models.py");
                setActiveFile("service.py");
                void runInspect("models.py", "custom", CUSTOM_INSECURE_TEMPLATE);
              }}
              className={`rounded px-3 py-1.5 text-xs font-semibold transition ${
                sourceMode === "custom"
                  ? "bg-[#172a2e] text-[#fffdf8]"
                  : "border border-[#c9d1cf] bg-[#f8f4ec] text-[#3a494b]"
              }`}
            >
              Editable Sandbox (Insecure)
            </button>
            <button
              type="button"
              onClick={() => {
                setSourceMode("custom");
                setCustomFiles(CUSTOM_GUARDED_TEMPLATE);
                setTargetFile("models.py");
                setActiveFile("service.py");
                void runInspect("models.py", "custom", CUSTOM_GUARDED_TEMPLATE);
              }}
              className="rounded border border-[#9ec9b8] bg-[#e6f4ee] px-3 py-1.5 text-xs font-semibold text-[#0f7657] transition hover:bg-[#d7ede3]"
            >
              Editable Sandbox (Guarded 100/100)
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-12 md:items-end">
          <div className="md:col-span-4">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-[#5c6a67]">
              Target Module to Modify
              <select
                value={targetFile}
                onChange={(e) => {
                  setTargetFile(e.target.value);
                  void runInspect(e.target.value);
                }}
                className="mt-1.5 w-full rounded border border-[#b8af9f] bg-[#fffdf8] px-3 py-2 font-mono text-xs text-[#172a2e]"
              >
                {fileList.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="md:col-span-5">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-[#5c6a67]">
              Surgical Refactor Goal
              <input
                type="text"
                value={refactorTask}
                onChange={(e) => setRefactorTask(e.target.value)}
                className="mt-1.5 w-full rounded border border-[#b8af9f] bg-[#fffdf8] px-3 py-2 text-xs text-[#172a2e]"
              />
            </label>
          </div>
          <div className="md:col-span-3 flex gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() => void runInspect()}
              className="flex flex-1 items-center justify-center gap-1.5 rounded border border-[#172a2e] bg-[#172a2e] px-3 py-2 text-xs font-semibold text-[#fffdf8] transition hover:border-[#bd513d] hover:bg-[#bd513d] disabled:opacity-50"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
              <span>Re-Scan AST</span>
            </button>
            <button
              type="button"
              disabled={applying}
              onClick={() => void runApplyPreview()}
              className="flex items-center justify-center gap-1.5 rounded border border-[#0f7657] bg-[#0f7657] px-3 py-2 text-xs font-semibold text-white transition hover:bg-[#0b5c43] disabled:opacity-50"
            >
              <Wand2 size={13} />
              <span>{applying ? "Applying..." : "Apply Fixes"}</span>
            </button>
          </div>
        </div>

        {error && (
          <p className="mt-3 rounded border border-[#dfb1a6] bg-[#fbece7] px-3 py-2 text-xs text-[#a93f35]">{error}</p>
        )}
      </section>

      {/* Before -> After Remediation Delta Banner */}
      {applyPreview && (
        <section className="editorial-card border-[#9ec9b8] bg-[#e6f4ee] p-5 text-[#172a2e]">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-[#0f7657]" />
              <div>
                <p className="font-mono text-xs font-bold uppercase tracking-wider text-[#0f7657]">
                  Stage 2 Remediation Verified · Health Score {applyPreview.beforeAudit.healthScore}/100 →{" "}
                  {applyPreview.afterAudit.healthScore}/100 (+{applyPreview.scoreDelta})
                </p>
                <p className="mt-1 text-xs text-[#2b3c39]">
                  Resolved {applyPreview.findingsResolved} security finding(s) across{" "}
                  {applyPreview.appliedDiffs.length} patched file(s), verified cleanly on re-scan by{" "}
                  <code className="font-mono">CodebaseAuditor</code>.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setSourceMode("custom");
                setCustomFiles(applyPreview.afterInspect.files);
                setData(applyPreview.afterInspect);
              }}
              className="rounded border border-[#0f7657] bg-[#fffdf8] px-3 py-1.5 font-mono text-xs font-semibold text-[#0f7657] hover:bg-[#0f7657] hover:text-white"
            >
              Load Remediated Repo into Sandbox
            </button>
          </div>

          {applyPreview.appliedDiffs.length > 0 && (
            <div className="mt-4 space-y-2">
              {applyPreview.appliedDiffs.map((item) => (
                <CommandBlock
                  key={item.filePath}
                  title={`APPLIED UNIFIED DIFF · ${item.filePath}`}
                  language="diff"
                  code={item.diff}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              title="Security Health Score"
              value={`${data.audit.healthScore}/100`}
              subtitle={`${data.audit.findings.length} static finding(s)`}
              accent={data.audit.healthScore >= 85 ? "emerald" : "terracotta"}
            />
            <StatCard
              title="Files Audited"
              value={data.audit.totalFiles}
              subtitle={`${data.symbols.length} AST symbols indexed`}
            />
            <StatCard
              title="HTTP Routes Indexed"
              value={data.audit.totalRoutesDetected}
              subtitle="Extracted from AST decorators"
              accent="cobalt"
            />
            <StatCard
              title="Test Modules Found"
              value={data.audit.totalTestsDetected}
              subtitle={data.audit.totalTestsDetected > 0 ? "Regression suite mapped" : "Missing coverage"}
              accent="emerald"
            />
          </div>

          <AstDependencyGraph
            files={fileList}
            edges={data.edges ?? []}
            selectedTarget={data.selectedTarget}
            blastRadius={data.blastRadius}
            onSelectFile={(dep) => {
              setTargetFile(dep);
              setActiveFile(dep);
              void runInspect(dep);
            }}
          />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Left: Blast Radius & Security Audit */}
            <div className="space-y-6 lg:col-span-7">
              <BlastRadiusCard
                blastRadius={data.blastRadius}
                onSelectFile={(dep) => {
                  setTargetFile(dep);
                  setActiveFile(dep);
                  void runInspect(dep);
                }}
              />

              <section className="editorial-card p-5">
                <div className="flex items-center justify-between border-b border-[#e5ddd0] pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldAlert size={16} className="text-[#bd513d]" />
                    <h3 className="text-sm font-semibold text-[#172a2e]">CodebaseAuditor Findings</h3>
                  </div>
                  <span className="font-mono text-xs text-[#5c6a67]">{data.audit.summary}</span>
                </div>

                {data.audit.findings.length === 0 ? (
                  <p className="mt-4 text-xs text-[#0f7657]">Zero secrets or missing guardrails detected.</p>
                ) : (
                  <div className="mt-4 space-y-3">
                    {data.audit.findings.map((finding, idx) => (
                      <div key={idx} className="rounded border border-[#dfb1a6] bg-[#fff8f5] p-3.5 text-xs">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="inline-flex items-center gap-1.5 font-mono font-bold text-[#a93f35]">
                            <AlertOctagon size={13} /> [{finding.severity}] {finding.category}
                          </span>
                          <button
                            type="button"
                            onClick={() => setActiveFile(finding.filePath)}
                            className="font-mono text-[11px] text-[#263aa8] underline"
                          >
                            {finding.filePath}:{finding.lineNumber}
                          </button>
                        </div>
                        <p className="mt-1.5 font-medium text-[#172a2e]">{finding.description}</p>
                        <p className="mt-1 text-[#47534e]">
                          <strong>Remediation:</strong> {finding.remediation}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>

            {/* Right: Source File Viewer / Sandbox Editor + Surgical Patches */}
            <div className="space-y-6 lg:col-span-5">
              <section className="editorial-card p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e5ddd0] pb-3">
                  <div className="flex items-center gap-2">
                    <FileCode2 size={15} className="text-[#172a2e]" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#172a2e]">
                      Repository Source ({activeFile})
                    </h3>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {fileList.map((fname) => (
                    <button
                      key={fname}
                      type="button"
                      onClick={() => setActiveFile(fname)}
                      className={`rounded px-2 py-1 font-mono text-[11px] ${
                        activeFile === fname
                          ? "bg-[#172a2e] text-[#fffdf8]"
                          : "border border-[#d6cec0] bg-[#f8f4ec] text-[#3a494b]"
                      }`}
                    >
                      {fname}
                    </button>
                  ))}
                </div>

                <div className="mt-3">
                  {sourceMode === "custom" ? (
                    <textarea
                      rows={11}
                      value={customFiles[activeFile] ?? ""}
                      onChange={(e) =>
                        setCustomFiles((prev) => ({
                          ...prev,
                          [activeFile]: e.target.value,
                        }))
                      }
                      aria-label={`Edit ${activeFile}`}
                      className="w-full rounded border border-[#1d2b30] bg-[#142025] p-3 font-mono text-xs leading-relaxed text-[#eaf1f0]"
                    />
                  ) : (
                    <CommandBlock
                      title={activeFile}
                      language="python"
                      code={data.files[activeFile] ?? "# Select a file above"}
                    />
                  )}
                </div>
              </section>

              <section className="editorial-card p-5">
                <div className="flex items-center gap-2 border-b border-[#e5ddd0] pb-3">
                  <GitFork size={15} className="text-[#0f7657]" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#172a2e]">
                    Synthesized Surgical Refactor Plan
                  </h3>
                </div>
                <p className="mt-2.5 text-xs text-[#3a494b]">{data.refactorPlan.verificationStrategy}</p>
                <div className="mt-3 space-y-3">
                  {data.refactorPlan.patches.map((patch, idx) => (
                    <CommandBlock
                      key={idx}
                      title={`${patch.changeType.toUpperCase()} · ${patch.filePath}`}
                      language="diff"
                      code={patch.diffOrContent}
                    />
                  ))}
                </div>
              </section>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
