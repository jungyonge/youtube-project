# Phase 4: 대본 생성 + 정책 검수

## 목표
EvidencePack을 기반으로 Gemini로 대본을 생성하고, ChatGPT로 검수 + 정책 검수를 거친 뒤,
민감 주제는 Human Approval 게이트로 승인 대기한다.

---

## 구현 항목

### 21. gemini_client.py

**파일**: `app/services/gemini_client.py`

```python
"""
Google Gemini API 클라이언트.

class GeminiClient:
    def __init__(settings):
        - google-genai SDK 초기화
        - model: settings.GEMINI_MODEL

    @retry_api_call
    async def generate(prompt, system_instruction=None, temperature=0.7) -> GeminiResponse:
        - API 호출
        - 입력/출력 토큰 수 추적
        - CostLog 기록용 데이터 반환

    @retry_api_call
    async def generate_json(prompt, response_schema, ...) -> dict:
        - JSON 모드로 호출
        - 응답을 Pydantic 모델로 파싱

GeminiResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float  # 단가 기반 자동 계산
"""
```

### 22. prompts.py

**파일**: `app/utils/prompts.py`

```python
"""
프롬프트 템플릿 중앙 관리.

SCRIPT_GENERATION_PROMPT:
  - 근거팩 기반 대본 생성
  - 구조: Hook → Intro → Body (3~5 포인트) → Conclusion
  - 에셋 전략: generated_image 최대 50%, 나머지는 카드/차트
  - 근거 매핑: claim_text, claim_type, evidence_source_id, confidence
  - 정책 플래그: 주식예측, 정치인, 의료조언, 논란성주장
  - 민감도 판정: low/medium/high
  - FullScript JSON 출력

SCRIPT_REVIEW_PROMPT:
  - claim_type 적절성 검수
  - policy_flags 누락 확인
  - overall_sensitivity 재판정
  - disclaimer 씬 자동 추가 (투자 조언 감지 시)

POLICY_REVIEW_PROMPT:
  - 주식: 단정적 투자 표현 → 완화 표현 수정
  - 정치: 일방적 지지/비난 → 반대 관점 추가
  - 의료: 의료 조언 → "전문가 상담" disclaimer
  - 명예훼손 소지 표현 제거

KEY_CLAIMS_EXTRACTION_PROMPT:
  - EvidencePack 핵심 주장 5~10개 추출 (step1c에서 사용)
"""
```

### 23. step2_research.py (Gemini 대본 생성)

**파일**: `app/pipeline/steps/step2_research.py`

```python
"""
Celery Task: research_task

Input: job_id
Flow:
1. S3에서 EvidencePack 로드
2. SCRIPT_GENERATION_PROMPT 렌더링
   - topic, style, additional_instructions
   - key_claims, ranked_chunks, source_metadata
   - target_duration에 따른 씬 수 계산 (min/max)
3. GeminiClient.generate_json() 호출 → FullScript 파싱
4. 파싱 실패 시 1회 재시도 (프롬프트 보강)
5. FullScript JSON을 S3에 저장
6. CostLog 기록
7. JobStepExecution 완료 (progress 35%)

비용 체크:
- 호출 전 현재 누적 비용 확인
- 예산 80% 초과 시 Gemini Pro → Flash 다운그레이드
"""
```

### 24. openai_client.py

**파일**: `app/services/openai_client.py`

```python
"""
OpenAI API 클라이언트 (ChatGPT, TTS, DALL-E).

class OpenAIClient:
    def __init__(settings):
        - openai SDK 초기화

    @retry_api_call
    async def chat(messages, model=None, temperature=0.3, response_format=None) -> ChatResponse:
        - ChatGPT API 호출
        - 토큰 수 + 비용 추적

    @retry_api_call
    async def tts(text, voice, model=None) -> bytes:
        - TTS API 호출
        - 오디오 바이트 반환
        - 글자 수 기반 비용 계산

    @retry_api_call
    async def generate_image(prompt, size=None, quality="standard") -> bytes:
        - DALL-E 3 API 호출
        - 이미지 URL → 다운로드 → bytes 반환
        - 건당 비용 기록

ChatResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float
"""
```

### 25. step3_review.py (ChatGPT 대본 검수)

**파일**: `app/pipeline/steps/step3_review.py`

```python
"""
Celery Task: review_task

Input: job_id
Flow:
1. S3에서 FullScript JSON 로드
2. SCRIPT_REVIEW_PROMPT + FullScript JSON을 GPT-4o에 전송
3. 검수 결과:
   - claim_type 수정 (fact인데 근거 없으면 → inference)
   - policy_flags 누락 보완
   - overall_sensitivity 재판정
   - 투자 조언 감지 시 disclaimer 씬 자동 추가
4. 수정된 FullScript를 S3에 저장 (덮어쓰기)
5. CostLog 기록
6. JobStepExecution 완료 (progress 45%)
"""
```

### 26. step3b_policy_review.py (정책 검수)

**파일**: `app/pipeline/steps/step3b_policy_review.py`

```python
"""
Celery Task: policy_review_task

Input: job_id
Flow:
1. S3에서 FullScript 로드
2. policy_flags가 1개 이상인 씬만 추출
3. 없으면 skip (progress 50%로 갱신 후 종료)
4. POLICY_REVIEW_PROMPT + 플래그된 씬들을 GPT-4o에 전송

검수 내용:
- 주식: "~할 것이다" → "~할 가능성이 있습니다"
  + 영상 시작에 투자 면책 disclaimer 씬 삽입
- 정치: 일방적 지지/비난 → 반대 관점 포함 씬 추가
  + 명예훼손 소지 표현 제거
- 의료: "~하면 낫는다" → "전문가와 상담하세요" disclaimer
- fact/inference/opinion 라벨이 나레이션에 반영되는지 확인

5. 수정된 FullScript S3 저장
6. is_sensitive_topic 갱신
7. CostLog 기록
8. JobStepExecution 완료 (progress 50%)
"""
```

### 27. step3c_human_gate.py (Human Approval 게이트)

**파일**: `app/pipeline/steps/step3c_human_gate.py`

```python
"""
Celery Task: human_gate_task

Input: job_id
Flow:
1. VideoJob 로드
2. 조건 확인:
   - overall_sensitivity == "high" → 승인 필요
   - auto_approve == False → 승인 필요
   - 둘 다 아니면 → skip (바로 통과)
3. 승인 필요 시:
   a. 대본 JSON presigned URL 생성
   b. job.phase = "awaiting_approval"
   c. job.requires_human_approval = True
   d. SSE로 "approval_required" 이벤트 전송
      { script_preview_url, sensitivity_level }
   e. Celery task 종료 (파이프라인 일시 중지)
4. 24시간 timeout → periodic task에서 자동 취소

진행률: 55% (승인 대기 시 여기서 멈춤)
"""
```

### 28. Approve/Reject API 라우트

**파일**: `app/api/routes/video.py`에 추가

```
POST /api/v1/videos/{job_id}/approve
  Auth: 소유자만
  Flow:
    1. job.human_approved = True
    2. job.phase = "approved"
    3. Celery task 체인 재개 (asset_generation부터)
    4. SSE "progress" 이벤트

POST /api/v1/videos/{job_id}/reject
  Auth: 소유자만
  Flow:
    1. job.human_approved = False
    2. job.phase = "rejected"
    3. SSE "cancelled" 이벤트
    4. 사용자에게 대본 수정 후 재요청 안내
```

### 파이프라인 모델

**파일**: `app/pipeline/models/assets.py`

```python
class SceneAssetPlan(BaseModel):
    """
    씬별 최적 에셋 전략. DALL-E 이미지만이 아니라 다양한 유형 혼합.
    """
    asset_type: Literal[
        "generated_image",    # DALL-E 생성 이미지
        "quote_card",         # 인용문 카드 (템플릿 기반)
        "data_chart",         # 차트/그래프 (matplotlib/Pillow)
        "timeline_card",      # 타임라인 카드
        "title_card",         # 제목/섹션 구분 카드
        "web_capture",        # 원본 웹페이지 스크린샷 (Playwright)
        "text_overlay",       # 핵심 키워드 강조 화면
        "split_screen",       # 비교 화면 (좌/우)
    ]
    generation_prompt: str | None = None      # generated_image 전용
    template_id: str | None = None            # 카드 템플릿 ID
    template_data: dict | None = None         # 템플릿에 채울 데이터
    fallback_strategy: Literal["placeholder", "text_overlay", "skip"] = "placeholder"
    priority: int = 1                         # 예산 부족 시 낮은 priority부터 생략
```

**파일**: `app/pipeline/models/script.py`

```python
class SceneClaim(BaseModel):
    claim_text: str
    claim_type: Literal["fact", "inference", "opinion"]
    evidence_source_id: str
    evidence_quote: str | None
    confidence: float

class SceneCitation(BaseModel):
    source_domain: str
    source_title: str
    display_text: str             # "출처: 조선일보 (2026.03.28)"

class ScriptScene(BaseModel):
    scene_id: int
    section: str          # hook|intro|body_N|conclusion
    purpose: str          # 이 씬의 목적 (한 줄)
    duration_target_sec: int
    duration_actual_sec: int | None
    narration: str
    subtitle_chunks: list[str]    # 자막 분절 (20자 단위)

    # 에셋 계획 (다양한 유형)
    asset_plan: list[SceneAssetPlan]

    # 전환 효과
    transition_in: str | None     # 이 씬으로 들어올 때
    transition_out: str | None    # 이 씬에서 나갈 때

    # 근거/정책
    claims: list[SceneClaim]
    citations: list[SceneCitation]
    policy_flags: list[str]       # 아래 정책 플래그 참조
    keywords: list[str]

class FullScript(BaseModel):
    title: str
    subtitle: str
    total_duration_sec: int
    thumbnail_prompt: str
    scenes: list[ScriptScene]
    tags: list[str]
    description: str

    # 정책 메타
    overall_sensitivity: Literal["low", "medium", "high"] = "low"
    requires_human_approval: bool = False
    policy_warnings: list[str] = []
```

### 정책 플래그 (policy_flags) 전체 목록

| 플래그 | 트리거 조건 |
|--------|-------------|
| `contains_stock_prediction` | 주식/투자 수익률 예측 |
| `mentions_politician` | 특정 정치인 이름 언급 |
| `contains_medical_advice` | 건강/의료 조언 |
| `controversial_claim` | 논란성 주장 (팩트 아닌 강한 주장) |

### 민감도 판정 기준 (overall_sensitivity)

| 수준 | 대상 주제 | 처리 |
|------|-----------|------|
| **low** | 기술, 교육, 일반 정보 | 자동 통과 |
| **medium** | 경제 전망, 사회 이슈 | 자동 통과 (policy_review 실행) |
| **high** | 정치 논쟁, 투자 조언, 의료 | `requires_human_approval = true` → Human Gate 대기 |

### Disclaimer 씬 자동 삽입

정책 검수 시 아래 조건에 해당하면 영상 **시작 부분**에 disclaimer 씬을 자동 삽입:
- `contains_stock_prediction` → "이 영상은 투자 권유가 아닙니다" 면책 조항
- `contains_medical_advice` → "전문의와 상담하세요" 면책 조항
- 삽입된 씬은 `section="disclaimer"`, `asset_type="title_card"`

---

## 선행 조건
- Phase 3 완료 (EvidencePack이 S3에 존재해야 함)

## 완료 기준
- [ ] Gemini 클라이언트로 대본 생성 성공 (FullScript JSON 파싱)
- [ ] ChatGPT 검수 후 claim_type 수정, policy_flags 보완
- [ ] 민감 주제 정책 검수 — disclaimer 씬 삽입 확인
- [ ] Human gate — sensitivity=high일 때 파이프라인 정지
- [ ] `POST /approve` → 파이프라인 재개
- [ ] `POST /reject` → 작업 종료
- [ ] 모든 API 호출에 CostLog 기록
