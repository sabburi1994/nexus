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

// Stage 1: Closed-Loop Self-Healing Contracts
export interface HealingAttemptContract {
  attemptNumber: number;
  testFailures: string[];
  diagnosis: string;
  diffApplied: string;
  retestPassed: boolean;
  timestamp: string;
}

export interface SelfHealingReportContract {
  initialTestsPassed: boolean;
  totalAttempts: number;
  maxAttemptsAllowed: number;
  finalStatus: "HEALTHY" | "HEALED" | "EXHAUSTED";
  attempts: HealingAttemptContract[];
  durationSeconds: number;
  summary: string;
}

// Stage 2: Brownfield Legacy Codebase Support Contracts
export interface SymbolDefinitionContract {
  name: string;
  kind: "class" | "function" | "route";
  filePath: string;
  lineNumber: number;
  routePath?: string;
  httpMethod?: string;
}

export interface BlastRadiusContract {
  target: string;
  riskTier: "LOW" | "MEDIUM" | "HIGH";
  directDependents: string[];
  indirectDependents: string[];
  affectedRoutes: string[];
  affectedTests: string[];
  totalAffectedFiles: number;
}

export interface SecurityFindingContract {
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  category: "SECRET_LEAK" | "PROMPT_INJECTION" | "MISSING_GUARDRAIL";
  filePath: string;
  lineNumber: number;
  description: string;
  remediation: string;
}

export interface CodebaseAuditReportContract {
  projectName: string;
  rootPath: string;
  totalFiles: number;
  healthScore: number;
  findings: SecurityFindingContract[];
  totalRoutesDetected: number;
  totalTestsDetected: number;
  hasCiWorkflow: boolean;
  hasDockerfile: boolean;
  hasTerraform: boolean;
  summary: string;
}

export interface FilePatchContract {
  filePath: string;
  diffOrContent: string;
  changeType: "modify" | "create" | "delete";
}

export interface RefactorPlanContract {
  task: string;
  targetFiles: string[];
  blastRadius: BlastRadiusContract;
  patches: FilePatchContract[];
  verificationStrategy: string;
  estimatedRisk: string;
}

// Stage 3: Team Telemetry & Enterprise ROI Contracts
export interface DoraMetricsContract {
  deploymentFrequencyMultiplier: number;
  leadTimeReductionPct: number;
  changeFailureRatePct: number;
  mttrMinutes: number;
}

export interface EnterpriseRoiContract {
  projectName: string;
  targetPath: string;
  timestamp: string;
  totalFilesAnalyzed: number;
  totalLinesOfCode: number;
  totalRunsAnalyzed: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalTokenCostUsd: number;
  engineeringHoursSaved: number;
  hourlyRateUsd: number;
  humanCostSavedUsd: number;
  netSavingsUsd: number;
  roiMultiplier: number;
  doraMetrics: DoraMetricsContract;
  vulnerabilitiesPrevented: number;
  healingCyclesExecuted: number;
  refactorTasksExecuted: number;
  summary: string;
}
