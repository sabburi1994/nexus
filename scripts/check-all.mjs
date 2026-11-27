#!/usr/bin/env node
/**
 * Unified local verification runner for the Nexus monorepo.
 *
 * Runs Python (ruff, mypy, core pytest, showcase pytest) and TypeScript/React
 * (all 5 npm packages build + tokens/ui typecheck & vitest) in one command.
 *
 * Usage:
 *   npm run check:all
 *   node scripts/check-all.mjs --python-only
 *   node scripts/check-all.mjs --js-only
 */

import { spawnSync } from "node:child_process";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = new Set(process.argv.slice(2));
const runPython = !args.has("--js-only");
const runJs = !args.has("--python-only");

const pythonBin = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const npmBin = process.platform === "win32" ? "npm.cmd" : "npm";
const isWin = process.platform === "win32";

/** @type {Array<{ name: string; cmd: string; args: string[]; env?: Record<string, string> }>} */
const steps = [];

if (runPython) {
  const srcPath = path.join(ROOT, "src");
  const pyEnv = {
    ...process.env,
    PYTHONPATH: process.env.PYTHONPATH ? `${srcPath}${path.delimiter}${process.env.PYTHONPATH}` : srcPath,
  };
  steps.push(
    { name: "ruff check", cmd: pythonBin, args: ["-m", "ruff", "check", "src", "tests", "apps/showcase/backend", "benchmarks"] },
    { name: "ruff format --check", cmd: pythonBin, args: ["-m", "ruff", "format", "--check", "src", "tests", "apps/showcase/backend", "benchmarks"] },
    { name: "mypy src", cmd: pythonBin, args: ["-m", "mypy", "src"] },
    { name: "pytest core", cmd: pythonBin, args: ["-m", "pytest", "-o", "pythonpath=src", "tests/"] },
    { name: "pytest showcase", cmd: pythonBin, args: ["-m", "pytest", "apps/showcase/backend/tests/"], env: pyEnv },
  );
}

if (runJs) {
  steps.push(
    { name: "npm build:packages", cmd: npmBin, args: ["run", "build:packages"] },
    { name: "tokens typecheck", cmd: npmBin, args: ["run", "typecheck", "-w", "@nexus-agent-framework/tokens"] },
    { name: "tokens test", cmd: npmBin, args: ["run", "test", "-w", "@nexus-agent-framework/tokens"] },
    { name: "ui typecheck", cmd: npmBin, args: ["run", "typecheck", "-w", "@nexus-agent-framework/ui"] },
    { name: "ui test", cmd: npmBin, args: ["run", "test", "-w", "@nexus-agent-framework/ui"] },
  );
}

/** @type {Array<{ name: string; ok: boolean; seconds: number }>} */
const results = [];
let failed = false;

for (const step of steps) {
  console.log(`\n==> ${step.name}`);
  const started = performance.now();
  const res = spawnSync(step.cmd, step.args, {
    cwd: ROOT,
    env: step.env ?? process.env,
    stdio: "inherit",
    shell: isWin && step.cmd.endsWith(".cmd"),
  });
  const seconds = (performance.now() - started) / 1000;
  const ok = res.status === 0;
  results.push({ name: step.name, ok, seconds });
  if (!ok) {
    failed = true;
    break;
  }
}

console.log("\n=== Nexus check-all summary ===");
for (const r of results) {
  console.log(`  [${r.ok ? "PASS" : "FAIL"}] ${r.name.padEnd(22)} ${r.seconds.toFixed(1)}s`);
}

process.exit(failed ? 1 : 0);
