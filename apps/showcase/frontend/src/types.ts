import type {
  BlastRadiusContract,
  CodebaseAuditReportContract,
  DoraMetricsContract,
  EnterpriseRoiContract,
  RefactorPlanContract,
  SelfHealingReportContract,
  SymbolDefinitionContract,
} from "@nexus-agent-framework/contracts";
import type { TraceStep } from "@nexus-agent-framework/ui";

export type WorkspaceTab = "overview" | "simulator" | "brownfield" | "telemetry" | "docs" | "packages";
export type DocTopic = "quickstart" | "cli" | "mcp" | "orchestrators" | "python-sdk" | "packages";

export interface SuiteVerificationStat {
  passed: number;
  total: number;
  command: string;
}

export interface FrameworkHealth {
  status: string;
  framework: string;
  version: string;
  pypi_live_version?: string;
  pypi_staged_version?: string;
  ci_status_url?: string;
  website: string;
  repository: string;
  author: string;
  tests_passed: number;
  tests_total: number;
  suite_breakdown?: Record<string, SuiteVerificationStat>;
  preflight_clearance: string;
  supported_models: string[];
  default_model: string;
  mcp_enabled: boolean;
  stages_active: string[];
  packages: Record<string, string>;
  pricing_model: Record<string, string>;
}

export interface SimulationResponse {
  run_id: string;
  execution_mode: "deterministic" | "byok-live";
  actual_api_cost_usd: number;
  projected_gemini_cost_usd: number;
  app_name: string;
  title: string;
  tagline: string;
  target_cloud: string;
  sanitized_input: string;
  pii_scrubbed_count: number;
  user_stories: string[];
  steps: TraceStep[];
  total_tokens: number;
  total_cost_usd: number;
  healing_cycles: number;
  verdict: string;
  healing_report: SelfHealingReportContract;
  roi_report: EnterpriseRoiContract;
  artifacts: {
    wireframe_html: string;
    architecture_md: string;
    backend_main_py: string;
    backend_models_py: string;
    frontend_app_tsx: string;
    sql_ddl: string;
    terraform_main_tf: string;
    test_preflight_py: string;
  };
}

export interface AstEdge {
  source: string;
  target: string;
}

export interface BrownfieldInspectResponse {
  files: Record<string, string>;
  selectedTarget: string;
  symbols: SymbolDefinitionContract[];
  edges: AstEdge[];
  audit: CodebaseAuditReportContract;
  blastRadius: BlastRadiusContract;
  refactorPlan: RefactorPlanContract;
}

export interface BrownfieldApplyPreviewResponse {
  beforeAudit: CodebaseAuditReportContract;
  afterAudit: CodebaseAuditReportContract;
  afterInspect: BrownfieldInspectResponse;
  appliedDiffs: Array<{ filePath: string; diff: string }>;
  scoreDelta: number;
  findingsResolved: number;
}

export interface RoiApiResponse {
  team_size: number;
  hourly_rate: number;
  monthly_hours_saved: number;
  annual_hours_saved: number;
  monthly_gross_savings_usd: number;
  annual_gross_savings_usd: number;
  monthly_token_cost_usd: number;
  annual_net_savings_usd: number;
  roi_multiplier: number;
  dora_metrics: {
    deployment_frequency_multiplier: number;
    lead_time_reduction_pct: number;
    change_failure_rate_pct: number;
    mttr_minutes: number;
  };
  summary: string;
  scorecard: EnterpriseRoiContract;
  cli_summary: string;
}

export interface GuardrailInspectResponse {
  blocked: boolean;
  matched_pattern: string | null;
  sanitized_text: string;
  redactions_count: number;
  verdict: string;
}

export type { DoraMetricsContract, EnterpriseRoiContract, SelfHealingReportContract, BlastRadiusContract };
