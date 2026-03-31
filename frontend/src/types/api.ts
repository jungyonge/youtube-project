export type SourceType = "blog" | "news" | "youtube" | "custom_text";
export type VideoStyle = "informative" | "storytelling" | "tutorial" | "opinion";
export type ClaimType = "fact" | "inference" | "opinion";

export type JobPhase =
  | "queued"
  | "extracting"
  | "normalizing"
  | "building_evidence"
  | "generating_script"
  | "reviewing_script"
  | "policy_review"
  | "awaiting_approval"
  | "generating_assets"
  | "assembling_video"
  | "completed"
  | "failed"
  | "cancelled"
  | "rejected";

export const TERMINAL_STATES: JobPhase[] = [
  "completed",
  "failed",
  "cancelled",
  "rejected",
];

export interface SourceInput {
  url?: string;
  source_type: SourceType;
  custom_text?: string;
}

export interface VideoGenerationRequest {
  topic: string;
  sources: SourceInput[];
  style: VideoStyle;
  target_duration_minutes: number;
  language: string;
  tts_voice: string;
  include_subtitles: boolean;
  include_bgm: boolean;
  additional_instructions?: string;
  cost_budget_usd?: number;
  auto_approve: boolean;
  idempotency_key: string;
}

export interface JobStatusResponse {
  job_id: string;
  phase: JobPhase;
  progress_percent: number;
  current_step_detail: string;
  is_cancelled: boolean;
  requires_human_approval: boolean;
  human_approved: boolean | null;
  total_cost_usd: number;
  cost_budget_usd: number;
  attempt_count: number;
  parent_job_id: string | null;
  created_at: string;
  updated_at: string;
  download_url: string | null;
  script_preview_url: string | null;
}

export interface JobStepDetail {
  step_name: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  started_at: string | null;
  completed_at: string | null;
  duration_sec: number | null;
  cost_usd: number;
  error_message: string | null;
}

// SSE events
export type SSEEventType =
  | "progress"
  | "approval_required"
  | "cost_warning"
  | "completed"
  | "failed"
  | "cancelled";

export interface SSEProgressEvent {
  type: "progress";
  phase: JobPhase;
  progress_percent: number;
  current_step_detail: string;
  cost_usd: number;
}

export interface SSECompletedEvent {
  type: "completed";
  download_url: string;
  thumbnail_url: string;
  duration_sec: number;
  total_cost: number;
}

export interface SSEApprovalEvent {
  type: "approval_required";
  script_preview_url: string;
  sensitivity_level: "low" | "medium" | "high";
}

export interface SSECostWarningEvent {
  type: "cost_warning";
  current_cost: number;
  budget: number;
}

export interface SSEFailedEvent {
  type: "failed";
  error_message: string;
  last_completed_step: string;
  can_retry: boolean;
}

export interface SSECancelledEvent {
  type: "cancelled";
}

export type SSEEvent =
  | SSEProgressEvent
  | SSECompletedEvent
  | SSEApprovalEvent
  | SSECostWarningEvent
  | SSEFailedEvent
  | SSECancelledEvent;

// Script
export interface SceneClaim {
  claim_text: string;
  claim_type: ClaimType;
  evidence_source_id: string;
  evidence_quote: string | null;
  confidence: number;
}

export interface SceneAssetPlan {
  asset_type: string;
  generation_prompt: string | null;
  template_id: string | null;
  fallback_strategy: string;
  priority: number;
}

export interface ScriptScene {
  scene_id: number;
  section: string;
  purpose: string;
  duration_target_sec: number;
  duration_actual_sec: number | null;
  narration: string;
  asset_plan: SceneAssetPlan[];
  claims: SceneClaim[];
  policy_flags: string[];
  keywords: string[];
}

export interface FullScript {
  title: string;
  subtitle: string;
  total_duration_sec: number;
  scenes: ScriptScene[];
  tags: string[];
  description: string;
  overall_sensitivity: "low" | "medium" | "high";
  requires_human_approval: boolean;
  policy_warnings: string[];
}

// Admin
export interface AdminStats {
  today_jobs: number;
  success_rate: number;
  daily_cost_usd: number;
  active_jobs: number;
}

export interface AdminJobItem {
  job_id: string;
  user_email: string;
  topic: string;
  phase: JobPhase;
  total_cost_usd: number;
  created_at: string;
}

export interface DailyStatsItem {
  date: string;
  jobs: number;
  cost_usd: number;
  success_count: number;
  fail_count: number;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}
