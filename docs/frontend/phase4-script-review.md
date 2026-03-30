# Phase 4: 대본 생성 + 정책 검수

## 목표
Gemini 기반 대본 생성, ChatGPT 대본 검수, 민감 주제 정책 검수, Human Approval 게이트를 구현한다.

---

## 구현 항목

### 21. gemini_client.py + retry 적용

**파일**: `app/services/gemini_client.py`
- google-genai SDK 기반 Gemini API 클라이언트
- tenacity retry 데코레이터 적용

### 22. prompts.py (대본 생성 + 검수 + 정책 프롬프트)

**파일**: `app/utils/prompts.py`

대본 생성 프롬프트:
```python
SCRIPT_GENERATION_PROMPT = """
당신은 한국 유튜브 콘텐츠 전문 작가입니다.
아래 '근거팩(Evidence Pack)'을 분석하여 {target_duration}분 분량의 영상 대본을 작성하세요.

## 입력 정보
- 주제: {topic}
- 영상 스타일: {style}
- 추가 지시사항: {additional_instructions}

## 근거팩
### 핵심 주장 요약
{key_claims}

### 상위 근거 청크 (중요도 순)
{ranked_chunks_formatted}

### 출처 메타데이터
{source_metadata_formatted}

## 대본 작성 규칙

1. **구조**
   - Hook (0:00~0:30): 강렬한 오프닝
   - Intro (0:30~1:00): 주제 소개
   - Body (1:00~{body_end}): 3~5개 핵심 포인트
   - Conclusion ({body_end}~{total}): 요약 + CTA

2. **나레이션 톤**
   - 자연스러운 한국어 구어체
   - 번역체 절대 금지
   - 한 문장 40자 이내 권장 (TTS 최적화)

3. **씬 분할**
   - 씬당 30~60초, 총 {min_scenes}~{max_scenes}개

4. **에셋 전략 (중요)**
   모든 씬을 이미지 생성으로 채우지 말 것.
   씬의 내용에 따라 최적 asset_type을 선택:
   - 수치/통계 → "data_chart"
   - 인용/발언 → "quote_card"
   - 시간 순서 → "timeline_card"
   - 비교/대조 → "split_screen"
   - 분위기/장면 묘사 → "generated_image"
   - 섹션 전환 → "title_card"
   전체 씬 중 generated_image는 최대 50%.
   나머지는 카드/차트/텍스트 오버레이로 다양하게 구성.

5. **근거 매핑 (claims)**
   각 씬의 모든 주장에 대해:
   - claim_text: 주장 내용
   - claim_type: "fact" | "inference" | "opinion" 반드시 구분
   - evidence_source_id: 근거 출처 ID
   - confidence: 근거 확신도 (0~1)

6. **정책 플래그**
   아래에 해당하면 policy_flags에 추가:
   - 주식/투자 예측 → "contains_stock_prediction"
   - 특정 정치인 언급 → "mentions_politician"
   - 건강/의료 조언 → "contains_medical_advice"
   - 논란성 주장 → "controversial_claim"

7. **민감도 판정**
   전체 대본의 overall_sensitivity 판정:
   - "low": 기술, 교육, 일반 정보
   - "medium": 경제 전망, 사회 이슈
   - "high": 정치 논쟁, 투자 조언, 의료
   "high"이면 requires_human_approval = true

8. **팩트 체크**
   근거팩에 없는 내용 창작 금지.
   추정은 반드시 claim_type="inference"로 표시.

## 출력 형식
FullScript JSON 스키마를 정확히 따를 것.
"""
```

### 23. step2_research.py (Gemini 대본 생성)

**파일**: `app/pipeline/steps/step2_research.py`
- EvidencePack → FullScript 변환
- Gemini API 호출 (1M 토큰 컨텍스트 활용)

### 24. openai_client.py + retry 적용

**파일**: `app/services/openai_client.py`
- OpenAI API 클라이언트 (ChatGPT, DALL-E, TTS)
- tenacity retry 데코레이터 적용

### 25. step3_review.py (ChatGPT 검수)

**파일**: `app/pipeline/steps/step3_review.py`

```
추가 검수 항목:
- claims의 claim_type이 적절한지 (fact인데 근거 없으면 inference로 수정)
- policy_flags 누락 확인
- overall_sensitivity 재판정
- 투자 조언처럼 보이는 표현 → "이 영상은 투자 권유가 아닙니다" disclaimer 씬 자동 추가
```

### 26. step3b_policy_review.py (민감 주제 정책 검수)

**파일**: `app/pipeline/steps/step3b_policy_review.py`

```python
"""
정치, 주식, 시사 이슈는 별도 compliance review를 거친다.

검수 대상:
1. policy_flags가 1개 이상인 모든 씬

검수 내용:
- 주식: "~할 것이다", "반드시 오른다" 같은 단정적 투자 표현 →
  "~할 가능성이 있습니다" 등 완화 표현으로 수정
  + 영상 시작에 투자 면책 조항(disclaimer) 씬 삽입

- 정치: 특정 정치인/정당에 대한 일방적 지지/비난 →
  반대 관점도 포함하도록 씬 추가 요청
  + 명예훼손 소지 표현 제거

- 의료: "~하면 낫는다" 같은 의료 조언 →
  "전문가와 상담하세요" disclaimer 추가

- 모든 민감 씬: fact/inference/opinion 라벨이 나레이션에 반영되는지 확인
  (예: "전문가들은 ~로 분석합니다" vs "확실히 ~입니다")

구현:
- GPT-4o에게 policy review 전용 프롬프트로 검수 요청
- 수정된 대본 + 삽입된 disclaimer 씬 반환
- policy_flags 기반 자동 처리 + 로깅
"""
```

### 27. step3c_human_gate.py (승인 게이트)

**파일**: `app/pipeline/steps/step3c_human_gate.py`

```python
"""
overall_sensitivity == "high" 이거나,
사용자가 auto_approve=False로 요청한 경우:

1. 대본 JSON을 S3에 저장하고 presigned URL 생성
2. job.phase = "awaiting_approval"로 변경
3. SSE로 "승인 필요" 이벤트 전송
4. 파이프라인 일시 중지 (Celery task 종료)
5. 사용자가 POST /api/v1/videos/{job_id}/approve 호출 시 재개
6. 사용자가 POST /api/v1/videos/{job_id}/reject 호출 시 종료

timeout: 24시간 내 미승인 → 자동 취소
"""
```

### 28. approve/reject API 라우트

- `POST /api/v1/videos/{job_id}/approve` (human gate 승인)
- `POST /api/v1/videos/{job_id}/reject` (human gate 거부)

### 파이프라인 모델 (Pydantic)

**파일**: `app/pipeline/models/script.py`

```python
class SceneClaim(BaseModel):
    """씬 내 개별 주장과 근거 매핑"""
    claim_text: str
    claim_type: Literal["fact", "inference", "opinion"]
    evidence_source_id: str       # 근거 출처 Source.id
    evidence_quote: str | None    # 직접 인용 (있을 경우)
    confidence: float             # 근거 확신도 (0~1)

class SceneCitation(BaseModel):
    """화면에 표시할 출처 정보"""
    source_domain: str
    source_title: str
    display_text: str             # "출처: 조선일보 (2026.03.28)"

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
    generation_prompt: str | None = None  # generated_image 전용
    template_id: str | None = None        # 카드 템플릿 ID
    template_data: dict | None = None     # 템플릿에 채울 데이터
    fallback_strategy: Literal["placeholder", "text_overlay", "skip"] = "placeholder"
    priority: int = 1                     # 예산 부족 시 낮은 priority부터 생략

class ScriptScene(BaseModel):
    scene_id: int
    section: str                          # "hook", "intro", "body_1", ..., "conclusion"
    purpose: str                          # 이 씬의 목적 (한 줄)
    duration_target_sec: int
    duration_actual_sec: int | None = None  # TTS 실측 후 업데이트
    narration: str
    subtitle_chunks: list[str] = []       # 자막 분절 (20자 단위)

    # 에셋 계획 (다양한 유형)
    asset_plan: list[SceneAssetPlan]

    # 전환 효과
    transition_in: str | None = None      # 이 씬으로 들어올 때
    transition_out: str | None = None     # 이 씬에서 나갈 때

    # 근거/정책
    claims: list[SceneClaim] = []
    citations: list[SceneCitation] = []
    policy_flags: list[str] = []          # ["contains_stock_prediction", "mentions_politician"]

    # 키워드
    keywords: list[str] = []

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

---

## 선행 조건
- Phase 3 완료 (EvidencePack 생성 가능)

## 완료 기준
- [ ] Gemini 클라이언트 + retry 동작
- [ ] 대본 생성 프롬프트 적용 및 FullScript JSON 반환
- [ ] OpenAI 클라이언트 + retry 동작
- [ ] ChatGPT 대본 검수 (claim_type, policy_flags 보정) 동작
- [ ] 정책 검수 (주식/정치/의료 별도 처리) 동작
- [ ] Human gate (승인 대기 → 재개/거부) 동작
- [ ] approve/reject API 라우트 동작
- [ ] FullScript, ScriptScene, SceneClaim 등 Pydantic 모델 정의 완료
