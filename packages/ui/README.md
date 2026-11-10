# @nexus-agent-framework/ui

> **Shared React design system and observability components for AI agent applications.**

[![npm version](https://img.shields.io/npm/v/@nexus-agent-framework/ui.svg)](https://www.npmjs.com/package/@nexus-agent-framework/ui)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

`@nexus-agent-framework/ui` is a Tailwind-powered React component library specifically designed for AI-driven applications and agent observability:
- **`NexusHeader`**: Header bar with live model badge, dollar spend tracker, and budget ceiling.
- **`StatCard`**: High-contrast KPI tile with trend indicators (`up`, `down`, `neutral`).
- **`AiBadge`**: Model indicator showing active status, model name (e.g. Gemini 3.8 Flash), and thinking level.
- **`TraceViewer`**: Step-by-step agent execution timeline displaying token usage, dollar cost, and outputs.
- **`SecurityShieldBadge`**: Real-time indicator for prompt injection blocks and scrubbed PII secrets.

## Installation

```bash
npm install @nexus-agent-framework/ui
```

### Peer Dependencies
Ensure `react` and `react-dom` (>=18.0.0) and `tailwindcss` (>=3.0.0) are installed in your host project.

## Quickstart

```tsx
import React from "react";
import {
  NexusHeader,
  StatCard,
  AiBadge,
  TraceViewer,
  SecurityShieldBadge,
} from "@nexus-agent-framework/ui";

export function AppDashboard() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <NexusHeader
        appName="WatchHub"
        tagline="Verified European luxury watch index"
        activeModel="Gemini 3.8 Flash"
        budgetSpentUsd={0.0042}
        budgetCapUsd={1.0}
      />
      
      <main className="p-6 space-y-6">
        <div className="flex gap-4">
          <SecurityShieldBadge injectionsBlocked={3} piiScrubbed={12} />
          <AiBadge model="Gemini 3.8 Flash" status="active" thinkingLevel="medium" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard title="Active Listings" value="1,420" trend="up" trendValue="+14%" />
          <StatCard title="Scrape Latency" value="184ms" trend="down" trendValue="-22ms" />
          <StatCard title="Inference Cost" value="$0.0031" subtitle="98% under budget" />
        </div>
      </main>
    </div>
  );
}
```

## License

Licensed under the Apache 2.0 License. Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
