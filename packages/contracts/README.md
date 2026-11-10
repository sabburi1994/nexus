# @nexus-agent-framework/contracts

> **Universal TypeScript contracts, telemetry schemas, and architectural protocols for the Nexus Agent Framework.**

[![npm version](https://img.shields.io/npm/v/@nexus-agent-framework/contracts.svg)](https://www.npmjs.com/package/@nexus-agent-framework/contracts)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

`@nexus-agent-framework/contracts` defines the strongly typed boundaries between human users, autonomous agents, and cloud backends. It provides canonical interfaces for:
- **Agent Telemetry & Cost Events** (`AgentTelemetryEvent`)
- **Product Proposals & Requirements** (`ProductProposalContract`)
- **Solution Blueprints** (`SolutionBlueprintContract`)
- **Relational Data Architecture & DDL** (`DataArchitectureContract`)
- **DevOps & Terraform Specifications** (`DevopsSpecificationContract`)
- **QA Verification & Pre-flight Verdicts** (`QaSpecificationContract`)
- **Cryptographic Audit Chains** (`AuditChainEntryContract`)

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

Licensed under the Apache 2.0 License. Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
