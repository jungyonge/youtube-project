# Phase 3: 소스 처리 파이프라인

## 목표
콘텐츠 추출(블로그, 뉴스, YouTube), 소스 정규화/중복 제거, 근거팩 생성까지의
소스 처리 파이프라인을 구현한다.

---

## 구현 항목

### 16. retry.py (tenacity 공통 모듈)

**파일**: `app/utils/retry.py`
- tenacity 재시도 데코레이터 공통 모듈
- 외부 API 호출 시 필수 적용

### 17. content_extractor.py

**파일**: `app/services/content_extractor.py`
- Strategy 패턴 기반 콘텐츠 추출
- Blog: BeautifulSoup4 / newspaper3k
- News: newspaper3k
- YouTube: youtube-transcript-api + yt-dlp fallback
- 동적 페이지: Playwright

### 18. step1_extract.py (콘텐츠 추출)

**파일**: `app/pipeline/steps/step1_extract.py`
- Strategy 패턴, youtube-transcript-api 실패 시 yt-dlp fallback 포함

### 19. step1b_normalize.py (소스 정규화 + 중복 제거)

**파일**: `app/pipeline/steps/step1b_normalize.py`

```python
"""
추출된 소스를 그대로 모델에 넣지 않는다.
정규화 → 중복 제거 → 메타데이터 보강을 거친다.

1. canonical URL 생성
   - UTM 파라미터 제거
   - www/non-www 통일
   - URL fragment 제거

2. content_hash 생성
   - 본문 텍스트의 simhash 또는 md5
   - 같은 hash = 같은 기사의 재배포 → is_duplicate=True 마킹

3. 메타 보강
   - domain 추출 → 도메인 기반 reliability_score 부여
     (주요 언론사 0.9, 블로그 0.5, 알 수 없음 0.3)
   - published_at 파싱 및 정규화
   - 오래된 기사(30일 이상) 페널티

4. 광고성/홍보성 필터
   - 광고 키워드 비율이 20% 이상이면 warning flag

결과: Source 테이블에 정규화 정보 저장
"""
```

### 20. step1c_evidence_pack.py (청킹 + 랭킹 + 근거팩 생성)

**파일**: `app/pipeline/steps/step1c_evidence_pack.py`

```python
"""
'모든 소스를 한 번에 모델에 밀어넣기' 대신,
핵심 근거만 추출하여 EvidencePack을 만든다.

1. 청킹 (Chunking)
   - 블로그/뉴스: 문단 단위 (300~500자)
   - YouTube: 타임스탬프 구간 단위 (30초~1분)

2. 랭킹 (Ranking)
   각 청크에 아래 점수 부여:
   - relevance_score: topic과의 코사인 유사도 (TF-IDF 기반, 라이브러리: scikit-learn)
   - recency_score: 최신일수록 높음 (exp decay, 반감기 7일)
   - reliability_score: 출처 도메인 신뢰도
   - composite_score = 0.5*relevance + 0.3*recency + 0.2*reliability

3. 상위 N개 청크 선택
   - 기본값: 상위 30개 청크
   - Gemini 컨텍스트에 여유가 있어도 노이즈 줄이기 위해 제한

4. 핵심 주장 요약
   - Gemini flash로 빠르게 "이 소스들의 핵심 주장 5~10개" 추출
   - 대본 생성 시 구조 잡는 데 활용

결과: EvidencePack 생성 → step2로 전달
"""
```

### 파이프라인 모델 (Pydantic)

**파일**: `app/pipeline/models/evidence.py`

```python
class SourceChunk(BaseModel):
    """소스를 문단/구간 단위로 청킹한 결과"""
    source_id: str
    chunk_index: int
    text: str
    timestamp_start: float | None = None  # YouTube용
    timestamp_end: float | None = None

class RankedEvidence(BaseModel):
    """랭킹된 근거 조각"""
    chunk: SourceChunk
    relevance_score: float        # 주제 관련성 (0~1)
    recency_score: float          # 최신성 (0~1)
    reliability_score: float      # 출처 신뢰도 (0~1)
    composite_score: float        # 종합 점수
    is_duplicate: bool = False

class EvidencePack(BaseModel):
    """
    대본 생성 모델에 전달할 근거 팩.
    '모든 ExtractedContent를 한 번에 밀어넣기' 대신,
    정규화 → 중복 제거 → 청킹 → 랭킹을 거친 압축 결과물.
    """
    topic: str
    total_sources: int
    deduplicated_sources: int
    ranked_chunks: list[RankedEvidence]   # 점수 순 정렬
    key_claims: list[str]                 # 핵심 주장 요약 (모델 전처리)
    source_metadata: list[dict]           # 출처별 메타 (domain, date, author)
```

---

## 선행 조건
- Phase 1 완료 (DB 모델, S3 래퍼)
- Phase 2 완료 (API 라우트에서 Job 생성 가능)

## 완료 기준
- [ ] `retry.py` tenacity 데코레이터 동작
- [ ] Blog/News/YouTube 콘텐츠 추출 동작
- [ ] YouTube transcript 실패 시 yt-dlp fallback 동작
- [ ] 소스 정규화 (canonical URL, content_hash) 동작
- [ ] 중복 소스 감지 (is_duplicate 마킹) 동작
- [ ] 도메인 기반 reliability_score 부여 동작
- [ ] 청킹 (문단/타임스탬프 단위) 동작
- [ ] 랭킹 (composite_score 계산) 동작
- [ ] EvidencePack 생성 동작
- [ ] 핵심 주장 요약 (Gemini flash) 동작
