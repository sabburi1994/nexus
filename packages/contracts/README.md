# @nexus-agent-framework/contracts

> **Universal TypeScript contracts, telemetry schemas, and architectural protocols for the Nexus Agent Framework.**

- **Website & Live Simulator**: [nexus.abburi.info](https://nexus.abburi.info)
- **Interactive Docs**: [nexus.abburi.info/#docs](https://nexus.abburi.info/#docs)

[![npm version](https://img.shields.io/npm/v/@nexus-agent-framework/contracts.svg)](https://www.npmjs.com/package/@nexus-agent-framework/contracts)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

`@nexus-agent-framework/contracts` defines strongly typed boundaries between human engineers, autonomous agents, and cloud backends across greenfield delivery and brownfield governance:
- **Squad Specs**: `AgentTelemetryEvent`, `ProductProposalContract`, `SolutionBlueprintContract`, `DataArchitectureContract`, `DevopsSpecificationContract`, `QaSpecificationContract`, `AuditChainEntryContract`
- **Stage 1 · Closed-Loop Self-Healing**: `SelfHealingReportContract`, `HealingAttemptContract`
- **Stage 2 · Brownfield Legacy Codebases**: `BlastRadiusContract`, `CodebaseAuditReportContract`, `RefactorPlanContract`, `SecurityFindingContract`, `SymbolDefinitionContract`
- **Stage 3 · Enterprise Telemetry & ROI**: `EnterpriseRoiContract`, `DoraMetricsContract`

## Installation

```bash
npm install @nexus-agent-framework/contracts
```

## Quickstart

```typescript
import {
  AgentTelemetryEvent,
  ProductProposalContract,
  SolutionBlueprintContract,
} from "@nexus-agent-framework/contracts";

// Validate telemetry events from an active agent
function handleTelemetry(event: AgentTelemetryEvent) {
  console.log(`Agent ${event.agentName} [${event.role}] is ${event.status}`);
  console.log(`Tokens: ${event.inputTokens} in / ${event.outputTokens} out (Cost: \$${event.costUsd})`);
}
```

## License

Licensed under the Apache 2.0 License. Documentation & live sandbox at [nexus.abburi.info](https://nexus.abburi.info). Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
