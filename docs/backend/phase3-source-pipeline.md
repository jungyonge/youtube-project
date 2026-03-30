# Phase 3: 소스 처리 파이프라인

## 목표
사용자가 제출한 URL에서 콘텐츠를 추출하고, 정규화/중복 제거/청킹/랭킹을 거쳐
대본 생성에 최적화된 근거팩(EvidencePack)을 만든다.

---

## 구현 항목

### 16. retry.py (tenacity 공통 모듈)

**파일**: `app/utils/retry.py`

```python
"""
tenacity 기반 재시도 데코레이터 모음.

- retry_api_call: 외부 API 호출 전용
  - max_attempts=3
  - exponential backoff (2초 → 4초 → 8초)
  - retry 대상: RateLimitError, TimeoutError, 5xx 응답
  - 실패 시 loguru로 warning 로그

- retry_network: 네트워크 I/O 전용 (웹 크롤링 등)
  - max_attempts=3
  - wait_fixed=2초
  - retry 대상: ConnectionError, TimeoutError

모든 재시도에 before_sleep 콜백으로 로그 기록.
"""
```

### 17. content_extractor.py (Strategy 패턴)

**파일**: `app/services/content_extractor.py`

```python
"""
URL 유형에 따라 적절한 추출 전략을 선택하는 Strategy 패턴.

ExtractedContent:
    source_type: str
    url: str
    title: str | None
    author: str | None
    published_date: datetime | None
    text_content: str
    word_count: int
    extraction_method: str

Strategies:
1. BlogExtractor
   - newspaper3k로 본문 추출
   - 실패 시 BeautifulSoup fallback

2. NewsExtractor
   - newspaper3k 우선
   - 동적 페이지(SPA, JS 렌더링) → Playwright fallback
   - Playwright는 headless Chromium으로 페이지 완전 로드 후 추출

3. YouTubeExtractor
   - youtube-transcript-api로 자막 추출
   - 실패 시 yt-dlp fallback (자막 다운로드)
   - 자막 없으면 에러 (음성 인식은 범위 밖)

4. CustomTextExtractor
   - 사용자가 직접 입력한 텍스트 처리

ContentExtractorService:
    async def extract(url, source_type) -> ExtractedContent
    - URL 파싱 → 전략 자동 선택
    - 추출 결과 + 메타데이터 반환
    - retry_network 데코레이터 적용
"""
```

### 18. step1_extract.py (콘텐츠 추출)

**파일**: `app/pipeline/steps/step1_extract.py`

```python
"""
Celery Task: extract_task

Input: job_id
Flow:
1. DB에서 VideoJob + Sources 조회
2. 각 Source URL에 대해 ContentExtractorService.extract() 호출
3. 추출된 콘텐츠를 S3에 스냅샷 저장 (content_snapshot_key)
4. Source 레코드 업데이트 (title, author, word_count, extraction_method)
5. JobStepExecution 레코드 생성/완료 처리
6. Redis PUBLISH로 진행 상태 전송 (progress 10%)

에러 처리:
- 개별 URL 추출 실패 → 해당 source만 skip (다른 소스 계속 진행)
- 모든 URL 실패 → step 실패 처리
- extraction_method에 사용된 방법 기록
"""
```

### 19. step1b_normalize.py (소스 정규화 + 중복 제거)

**파일**: `app/pipeline/steps/step1b_normalize.py`

```python
"""
Celery Task: normalize_task

Input: job_id (이전 step 결과는 S3에 저장되어 있음)
Flow:

1. Canonical URL 생성
   - UTM 파라미터 제거 (utm_source, utm_medium 등)
   - www/non-www 통일
   - URL fragment (#...) 제거
   - trailing slash 정규화

2. Content Hash 생성
   - 본문 텍스트의 MD5 해시
   - 같은 hash → is_duplicate=True 마킹

3. 메타 보강
   - domain 추출 → 도메인 기반 reliability_score 부여
     주요 언론사: 0.9
     전문 블로그: 0.7
     일반 블로그: 0.5
     알 수 없음: 0.3
   - published_at 파싱 및 정규화
   - 30일 이상 경과 기사 → recency 페널티

4. 광고성/홍보성 필터
   - 광고 키워드 비율이 설정값(config.AD_KEYWORD_THRESHOLD, 기본 20%) 이상 → warning flag

5. Source 테이블 업데이트
6. JobStepExecution 완료 처리 (progress 15%)
"""
```

### 20. step1c_evidence_pack.py (근거팩 생성)

**파일**: `app/pipeline/steps/step1c_evidence_pack.py`

```python
"""
Celery Task: evidence_pack_task

Input: job_id
Flow:

1. 청킹 (Chunking)
   - 블로그/뉴스: 문단 단위 (300~500자)
   - YouTube: 타임스탬프 구간 단위 (30초~1분)
   - SourceChunk 모델로 구조화

2. 랭킹 (Ranking)
   각 청크에 점수 부여:
   - relevance_score: topic과의 TF-IDF 코사인 유사도 (scikit-learn)
   - recency_score: 최신일수록 높음 (exp decay, 반감기 7일)
   - reliability_score: 출처 도메인 신뢰도 (Source 테이블에서 가져옴)
   - composite_score = 0.5*relevance + 0.3*recency + 0.2*reliability

3. 상위 N개 청크 선택
   - 기본값: 상위 30개 (설정 가능)
   - 노이즈 감소 목적

4. 핵심 주장 요약
   - Gemini Flash로 "이 소스들의 핵심 주장 5~10개" 추출
   - 빠른 요약이므로 flash 모델 사용

5. EvidencePack 생성 → S3 저장
6. JobStepExecution 완료 처리 (progress 20%)
"""
```

### 파이프라인 모델

**파일**: `app/pipeline/models/evidence.py`

```python
class SourceChunk(BaseModel):
    source_id: str
    chunk_index: int
    text: str
    timestamp_start: float | None = None
    timestamp_end: float | None = None

class RankedEvidence(BaseModel):
    chunk: SourceChunk
    relevance_score: float          # 0~1
    recency_score: float            # 0~1
    reliability_score: float        # 0~1
    composite_score: float
    is_duplicate: bool = False

class EvidencePack(BaseModel):
    topic: str
    total_sources: int
    deduplicated_sources: int
    ranked_chunks: list[RankedEvidence]
    key_claims: list[str]
    source_metadata: list[dict]
```

---

## 선행 조건
- Phase 1 완료 (DB 모델, S3 래퍼, config)
- Phase 2 완료 (API가 job을 생성해야 step이 실행 가능)

## 완료 기준
- [ ] `retry.py` — tenacity 데코레이터 동작 확인 (mock 테스트)
- [ ] `content_extractor.py` — 블로그/뉴스/YouTube URL 추출 성공
- [ ] `step1_extract.py` — 다수 소스 병렬 추출, 실패 소스 skip 처리
- [ ] `step1b_normalize.py` — 중복 URL 탐지, reliability_score 부여
- [ ] `step1c_evidence_pack.py` — TF-IDF 랭킹, 상위 N개 선택, 핵심 주장 요약
- [ ] EvidencePack JSON이 S3에 정상 저장
