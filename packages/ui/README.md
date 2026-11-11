# @nexus-agent-framework/ui

> **Shared React component library and institutional paper-and-ink design system for AI agent observability and Stage 1–3 workflows.**

- **Live Reference Implementation**: [nexus.abburi.info](https://nexus.abburi.info)
- **Interactive Simulator & Docs**: [nexus.abburi.info/#simulator](https://nexus.abburi.info/#simulator)

[![npm version](https://img.shields.io/npm/v/@nexus-agent-framework/ui.svg)](https://www.npmjs.com/package/@nexus-agent-framework/ui)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

`@nexus-agent-framework/ui` powers the Nexus Showcase Portal (`https://nexus.abburi.info`) and generated Nexus web applications with an institutional editorial palette (`paper` default theme, optional `dark` mode):
- **`NexusHeader`**: Sticky editorial masthead with workspace navigation items, live model badge, and budget spend tracker.
- **`StatCard`**: High-contrast KPI card with tabular numerals and delta badges.
- **`AiBadge`**: Active model status and thinking level chip.
- **`TraceViewer`**: Numbered vertical agent execution timeline displaying tokens, USD cost, and artifact previews.
- **`SecurityShieldBadge`**: Real-time prompt injection & secret scrubbing status pill.
- **`HealingLoopPanel`**: Stage 1 visualizer for closed-loop QA → patch → retest iterations.
- **`BlastRadiusCard`**: Stage 2 AST dependency impact, affected FastAPI routes, and regression test view.
- **`RoiScorecard`**: Stage 3 DORA velocity and financial return scorecard.
- **`CommandBlock`**: Ruled terminal/code snippet card with copy-to-clipboard support.

## Installation

```bash
npm install @nexus-agent-framework/ui
```

### Peer Dependencies
Ensure `react` and `react-dom` (`>=18.0.0`) and `tailwindcss` (`>=3.0.0`) are installed in your host project.

## Quickstart

```tsx
import React from "react";
import {
  NexusHeader,
  StatCard,
  AiBadge,
  TraceViewer,
  SecurityShieldBadge,
  HealingLoopPanel,
  BlastRadiusCard,
  RoiScorecard,
  CommandBlock,
} from "@nexus-agent-framework/ui";

export function AppDashboard() {
  return (
    <div className="min-h-screen bg-[#f5f1e8] text-[#172a2e]">
      <NexusHeader
        appName="WatchHub"
        tagline="Verified European luxury watch index"
        activeModel="Gemini 3.8 Flash"
        budgetSpentUsd={0.0042}
        budgetCapUsd={1.0}
      />
      <main className="mx-auto max-w-6xl space-y-6 p-6">
        <div className="flex flex-wrap gap-3">
          <SecurityShieldBadge injectionsBlocked={3} piiScrubbed={12} />
          <AiBadge model="Gemini 3.8 Flash" status="active" thinkingLevel="medium" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <StatCard title="Active Listings" value="1,420" trend="up" trendValue="+14%" />
          <StatCard title="Scrape Latency" value="184ms" trend="down" trendValue="-22ms" />
          <StatCard title="Inference Cost" value="$0.0031" subtitle="98% under budget" accent="emerald" />
        </div>
      </main>
    </div>
  );
}
```

## License

Licensed under the Apache 2.0 License. Live platform & documentation at [nexus.abburi.info](https://nexus.abburi.info). Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
