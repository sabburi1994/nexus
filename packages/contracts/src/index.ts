/**
 * @nexus/contracts
 * Universal data contracts and protocol definitions across sovereign apps and agents.
 */

export type ModelProvider = "vertex" | "google_ai" | "mock" | "ollama";

export type AgentRole =
  | "business_analyst"
  | "solution_architect"
  | "data_architect"
  | "ui_designer"
  | "fullstack_engineer"
  | "devops_engineer"
  | "qa_engineer"
  | "security_sentinel"
  | "custom";

export type PipelineStage =
  | "proposal"
  | "blueprint"
  | "data_schema"
  | "ui_specification"
  | "fullstack_implementation"
  | "iac_terraform"
  | "qa_verification"
  | "ready"
  | "failed";

export interface AgentTelemetryEvent {
  agentName: string;
  role: AgentRole;
  stage: PipelineStage;
  status: "idle" | "running" | "completed" | "error";
  summary: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  timestamp: string;
}

export interface ProductProposalContract {
  title: string;
  targetAudience: string;
  coreValueProposition: string;
  keyFeatures: string[];
  wireframeHtmlPreview?: string;
  estimatedCostPerRunUsd: number;
}

export interface SolutionBlueprintContract {
  architecturePattern: string;
  targetCloud: "gcp" | "aws" | "local";
  frontendTech: string;
  backendTech: string;
  databaseTech: string;
  apiEndpoints: Array<{ method: string; path: string; description: string }>;
  scalabilityNotes: string;
}

export interface DataArchitectureContract {
  tables: Array<{
    name: string;
    description: string;
    columns: Array<{ name: string; type: string; constraints?: string }>;
  }>;
  sqlDdl: string;
  migrationStrategy: string;
}

export interface FullStackSpecificationContract {
  backendCode: string;
  frontendCode: string;
  apiClientCode: string;
  runInstructions: string;
}

export interface DevopsSpecificationContract {
  terraformMainTf: string;
  terraformVariablesTf: string;
  dockerfile: string;
  ciCdYaml: string;
}

export interface QaSpecificationContract {
  unitTestsCode: string;
  integrationTestsCode: string;
  testRunnerCommand: string;
  verificationVerdict: "pass" | "conditional" | "fail";
}

export interface AuditChainEntryContract {
  entryId: string;
  previousHash: string;
  entryHash: string;
  actor: string;
  action: string;
  payload: Record<string, unknown>;
  timestamp: string;
}
