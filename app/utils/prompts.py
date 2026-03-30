"""프롬프트 템플릿 중앙 관리."""

SCRIPT_GENERATION_PROMPT = """당신은 한국 유튜브 콘텐츠 전문 작가입니다.
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
아래 JSON 스키마를 정확히 따를 것. JSON만 출력하고 다른 텍스트는 포함하지 마세요.

{{
  "title": "string",
  "subtitle": "string",
  "total_duration_sec": integer,
  "thumbnail_prompt": "string (DALL-E용 영어 프롬프트)",
  "scenes": [
    {{
      "scene_id": integer,
      "section": "hook|intro|body_1|body_2|...|conclusion",
      "purpose": "string",
      "duration_target_sec": integer,
      "narration": "string",
      "subtitle_chunks": ["string (20자 단위)"],
      "asset_plan": [
        {{
          "asset_type": "generated_image|quote_card|data_chart|timeline_card|title_card|text_overlay|split_screen",
          "generation_prompt": "string or null",
          "template_id": "string or null",
          "template_data": {{}} or null,
          "fallback_strategy": "placeholder|text_overlay|skip",
          "priority": integer
        }}
      ],
      "transition_in": "string or null",
      "transition_out": "string or null",
      "claims": [
        {{
          "claim_text": "string",
          "claim_type": "fact|inference|opinion",
          "evidence_source_id": "string",
          "evidence_quote": "string or null",
          "confidence": float
        }}
      ],
      "citations": [
        {{
          "source_domain": "string",
          "source_title": "string",
          "display_text": "string"
        }}
      ],
      "policy_flags": ["string"],
      "keywords": ["string"]
    }}
  ],
  "tags": ["string"],
  "description": "string",
  "overall_sensitivity": "low|medium|high",
  "requires_human_approval": boolean,
  "policy_warnings": ["string"]
}}
"""

SCRIPT_REVIEW_PROMPT = """당신은 유튜브 영상 대본 검수 전문가입니다.
아래 대본 JSON을 검수하고 수정된 전체 JSON을 반환하세요.

## 검수 항목
1. **claim_type 적절성**: fact인데 근거가 불충분하면 inference로 수정
2. **policy_flags 누락**: 아래 기준으로 누락된 플래그 추가
   - 주식/투자 예측 → "contains_stock_prediction"
   - 특정 정치인 언급 → "mentions_politician"
   - 건강/의료 조언 → "contains_medical_advice"
   - 논란성 주장 → "controversial_claim"
3. **overall_sensitivity 재판정**: 모든 policy_flags 고려하여 재판정
4. **disclaimer 추가**: 투자 조언이 감지되면 첫 씬 전에 disclaimer 씬 삽입
   - section: "disclaimer"
   - narration: "본 영상은 정보 제공 목적이며, 투자 권유가 아닙니다. 투자 판단은 본인 책임입니다."
5. **나레이션 품질**: 번역체, 어색한 표현 수정

## 대본 JSON
{script_json}

## 출력
수정된 전체 대본 JSON만 반환하세요. 설명 없이 JSON만 출력하세요.
"""

POLICY_REVIEW_PROMPT = """당신은 미디어 콘텐츠 정책 검수 전문가입니다.
policy_flags가 있는 씬들을 검수하고 수정된 전체 대본 JSON을 반환하세요.

## 정책 검수 규칙

### 주식/투자
- "~할 것이다", "반드시 오른다" 같은 단정적 투자 표현 → "~할 가능성이 있습니다" 등 완화 표현으로 수정
- 영상 시작에 투자 면책 disclaimer 씬 삽입

### 정치
- 특정 정치인/정당에 대한 일방적 지지/비난 → 반대 관점도 포함
- 명예훼손 소지 표현 제거

### 의료
- "~하면 낫는다" 같은 의료 조언 → "전문가와 상담하세요" disclaimer 추가

### 공통
- fact/inference/opinion 라벨이 나레이션에 적절히 반영되는지 확인
  (예: 사실은 "~입니다", 추론은 "~로 분석됩니다", 의견은 "~라는 견해가 있습니다")

## 대본 JSON
{script_json}

## 출력
수정된 전체 대본 JSON만 반환하세요.
"""

KEY_CLAIMS_EXTRACTION_PROMPT = """주제: {topic}

아래 자료에서 핵심 주장 5~10개를 한 줄씩 추출하세요.
번호를 붙이지 말고, 한 줄에 하나씩만 작성하세요.

{source_text}
"""
