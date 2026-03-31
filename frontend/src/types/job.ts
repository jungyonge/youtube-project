import type { JobPhase } from "./api";

/** JobPhase별 UI 색상 */
export const PHASE_COLORS: Record<JobPhase, string> = {
  queued: "bg-slate-100 text-slate-700",
  extracting: "bg-blue-100 text-blue-700",
  normalizing: "bg-blue-100 text-blue-700",
  building_evidence: "bg-blue-100 text-blue-700",
  generating_script: "bg-indigo-100 text-indigo-700",
  reviewing_script: "bg-indigo-100 text-indigo-700",
  policy_review: "bg-amber-100 text-amber-700",
  awaiting_approval: "bg-yellow-100 text-yellow-800",
  generating_assets: "bg-purple-100 text-purple-700",
  assembling_video: "bg-orange-100 text-orange-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-slate-100 text-slate-500",
  rejected: "bg-red-100 text-red-600",
};

/** JobPhase 한글 라벨 */
export const PHASE_LABELS: Record<JobPhase, string> = {
  queued: "대기 중",
  extracting: "콘텐츠 추출",
  normalizing: "소스 정규화",
  building_evidence: "근거 구축",
  generating_script: "대본 생성",
  reviewing_script: "대본 검수",
  policy_review: "정책 검토",
  awaiting_approval: "승인 대기",
  generating_assets: "에셋 생성",
  assembling_video: "영상 조립",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
  rejected: "거부됨",
};

/** Claim 뱃지 */
export const CLAIM_BADGES: Record<string, { color: string; label: string }> = {
  fact: { color: "bg-green-100 text-green-700", label: "사실" },
  inference: { color: "bg-yellow-100 text-yellow-700", label: "추론" },
  opinion: { color: "bg-orange-100 text-orange-700", label: "의견" },
};
