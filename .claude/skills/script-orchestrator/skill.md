---
name: script-orchestrator
description: "나레이션 대본 자동생성 오케스트레이터. 주제 또는 YouTube URL을 받아 researcher → scriptwriter → reviewer 3단계로 10분+ 나레이션 대본을 생성한다. '대본 만들어줘', '영상 스크립트', 'YouTube URL 분석해서 대본' 등에 사용한다. 단순 요약이나 번역은 이 스킬의 영역이 아니다."
---

# Script Orchestrator — 나레이션 대본 생성 파이프라인

유저의 주제 또는 YouTube URL을 받아, 3개 에이전트를 순차 호출하여 최종 FullScript JSON을 생성하는 오케스트레이터.

## 실행 모드

**에이전트 팀** — 3명이 순차적으로 작업

## 에이전트 구성

| 에이전트 | 파일 | 역할 | 순서 |
|---------|------|------|------|
| researcher | `.claude/agents/researcher.md` | 리서치 + EvidencePack 생성 | 1 |
| scriptwriter | `.claude/agents/scriptwriter.md` | 3막 구조 나레이션 대본 생성 | 2 |
| reviewer | `.claude/agents/reviewer.md` | 팩트체크 + 품질 검증 | 3 |

## 워크플로우

### Phase 0: 입력 파싱

1. 유저 입력에서 YouTube URL 감지: `(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})`
2. URL이면: `input_type = "youtube"`, `video_id` 추출
3. 아니면: `input_type = "topic"`, 주제 텍스트 그대로
4. 추가 파라미터 파싱:
   - `target_duration`: 기본 10분
   - `style`: 기본 "다큐멘터리" (뉴스/강의/에세이 등)
   - `character`: 기본 "elon_musk" (캐릭터 프리셋)
5. `_workspace/00_input.md`에 저장

### Phase 1: Researcher 호출

| 항목 | 내용 |
|------|------|
| **입력** | input_type, 주제 텍스트 또는 YouTube 자막 |
| **처리** | PRIMA 리서치, 핵심 주장 추출, 출처 수집 |
| **산출물** | `_workspace/01_research_brief.md` |
| **에러 시** | 에러 반환 (리서치 없이 대본 불가) |

- YouTube인 경우: `youtube-transcript-api`로 자막 추출 → researcher에 제공
- 주제인 경우: 주제 텍스트를 researcher에 직접 전달
- WebSearch/WebFetch 적극 활용

### Phase 2: Scriptwriter 호출

| 항목 | 내용 |
|------|------|
| **입력** | 01_research_brief.md + target_duration + style |
| **처리** | 서사 유형 판단, 3막 구조, 훅 조합, 나레이션 작성 |
| **산출물** | `_workspace/02_script_draft.json` (FullScript JSON 초안) |
| **에러 시** | temperature 낮추고(0.7→0.3) 1회 재시도 |

- 2,500단어 (10분 기준) 나레이션 생성
- 씬별 asset_plan + keywords 메타데이터 포함
- thumbnail_prompt, title, description 포함

### Phase 3: Reviewer 호출

| 항목 | 내용 |
|------|------|
| **입력** | 02_script_draft.json + 01_research_brief.md |
| **처리** | 팩트체크, 정책검수, 품질검증, 구조검증 |
| **산출물** | `_workspace/03_script_final.json` (FullScript JSON 최종) |
| **에러 시** | 초안을 최종본으로 사용 (reviewer는 선택적) |

- Critical 이슈: 즉시 수정 (최대 2회)
- Warning: 수정 권고 기록
- overall_sensitivity 재판정

### Phase 4: 후처리

1. `_review_summary` 필드 제거
2. `total_duration_sec` 재계산 (씬별 합산)
3. `FullScript.model_validate()`로 스키마 검증
4. S3 업로드: `{job_id}/script.json`

## 작업 규모별 모드

| 유저 요청 | 모드 | 에이전트 | 설명 |
|----------|------|---------|------|
| "대본 만들어줘" / URL 제공 | Full | 3명 모두 | 전체 파이프라인 |
| "리서치만 해줘" | Research | researcher만 | 리서치 브리프만 생성 |
| "이 리서치로 대본 써줘" | Script | scriptwriter + reviewer | 기존 리서치 활용 |
| "이 대본 검수해줘" | Review | reviewer만 | 기존 대본 검수 |

## 데이터 전달 프로토콜

| 전략 | 방법 | 용도 |
|------|------|------|
| 파일 기반 | `_workspace/` 디렉토리 | 주요 산출물 |
| 메시지 기반 | SendMessage | 실시간 상태 전달 |
| 태스크 기반 | TaskCreate/TaskUpdate | 진행률 추적 |

## 에러 핸들링

| 에러 유형 | Phase | 전략 |
|----------|-------|------|
| YouTube 자막 추출 실패 | 1 | 에러 반환 |
| 웹 검색 실패 | 1 | 일반 지식으로 폴백, "데이터 제한" 명시 |
| JSON 파싱 실패 | 2 | 스키마 재강조 후 1회 재시도 |
| 분량 미달/초과 | 2→3 | reviewer가 조정 |
| 팩트 검증 실패 | 3 | claim_type 강등 + 어미 완화 |

## 비용 관리

- 각 Phase의 토큰 사용량을 `cost_tracker`로 기록
- `budget_status.degrade_level >= 2` → Gemini Flash 모델 사용
- 리서치 웹 검색 최대 10회로 제한
