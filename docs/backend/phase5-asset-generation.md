# Phase 5: 자산 생성

## 목표
대본(FullScript)의 씬별 에셋 계획에 따라 TTS 오디오, 이미지(DALL-E + 카드/차트),
자막(SRT), BGM을 생성하고, 비용을 실시간 추적하여 예산 초과를 방지한다.

---

## 구현 항목

### 29. step4a_tts.py (ChatGPT TTS)

**파일**: `app/pipeline/steps/step4a_tts.py`

```python
"""
Celery Task: tts_task

Input: job_id
Flow:
1. S3에서 FullScript 로드
2. 각 씬의 narration 텍스트 추출
3. OpenAIClient.tts() 호출 (씬별)
   - voice: job.tts_voice (기본 "alloy")
   - model: settings.OPENAI_TTS_MODEL (기본 "tts-1-hd")
4. 오디오 파일 S3 업로드
   - key: {job_id}/audio/scene_{scene_id}.mp3
5. Asset 테이블 등록 (asset_type="tts_audio")
6. 실제 오디오 길이 측정 → scene.duration_actual_sec 업데이트
7. CostLog 기록 (글자수 기반 비용)
8. JobStepExecution 완료 (progress 65%)

에러 처리:
- 개별 씬 TTS 실패 → 3회 재시도 후 skip (무음 placeholder)
- 비용 예산 체크 후 초과 시 → 나머지 씬 skip
"""
```

### 30. step4b_images.py (다양한 에셋 생성)

**파일**: `app/pipeline/steps/step4b_images.py`

```python
"""
Celery Task: images_task

Input: job_id
Flow:
1. S3에서 FullScript 로드
2. 각 씬의 asset_plan 확인 → asset_type별 분기:

   "generated_image":
     - OpenAIClient.generate_image(prompt, size="1792x1024")
     - asyncio.Semaphore(MAX_CONCURRENT_IMAGE_REQUESTS) 로 동시 요청 제한
     - 비용: $0.08/장

   "quote_card":
     - Pillow + 템플릿 기반 인용문 카드 생성
     - template_data에서 quote_text, author, source 추출
     - 배경색/폰트/레이아웃 자동 적용
     - 비용: $0 (로컬 생성)

   "data_chart":
     - matplotlib로 차트 이미지 생성
     - template_data에서 chart_type, labels, values 파싱
     - 한글 폰트 적용 (NanumGothic)
     - 비용: $0

   "timeline_card":
     - Pillow 템플릿 기반 타임라인 카드
     - 비용: $0

   "title_card":
     - Pillow로 제목/섹션 구분 카드
     - 비용: $0

   "web_capture":
     - Playwright screenshot (원본 URL)
     - 실패 시 text_overlay fallback
     - 비용: $0

   "text_overlay":
     - Pillow로 키워드 강조 화면
     - 비용: $0

   "split_screen":
     - Pillow로 좌/우 비교 이미지 합성
     - 비용: $0

3. 모든 결과 1920x1080으로 리사이즈
4. S3 업로드 (key: {job_id}/images/scene_{scene_id}.png)
5. Asset 테이블 등록 (asset_type="scene_image")
6. CostLog 기록
7. JobStepExecution 완료 (progress 75%)

동시 요청 제한:
- asyncio.Semaphore(settings.MAX_CONCURRENT_IMAGE_REQUESTS)로 DALL-E 동시 요청 제한 (기본 5)

Cost Guardrail 적용 (4단계 자동 Degradation):
- 1단계 (예산 80%): DALL-E 이미지 수 50% 감소 (priority 낮은 씬 → text_overlay)
- 2단계 (예산 90%): Gemini Pro → Flash 다운그레이드
- 3단계 (예산 95%): 나머지 이미지 전부 text_overlay로 대체
- 4단계 (예산 100%): job 실패 처리 + 사용자에게 예산 부족 알림
- placeholder/text_overlay 사용 시 Asset.is_fallback = True

에러 처리:
- DALL-E 실패 → fallback_strategy 적용:
  "placeholder": 기본 이미지 사용
  "text_overlay": 키워드 텍스트 이미지 생성
  "skip": 이전 씬 이미지 재사용
"""
```

### 31. step4c_subtitles.py (SRT 자막)

**파일**: `app/pipeline/steps/step4c_subtitles.py`

```python
"""
Celery Task: subtitle_task

Input: job_id
Flow:
1. S3에서 FullScript 로드 + 각 씬의 duration_actual_sec 참조
2. 각 씬의 subtitle_chunks를 시간축에 배치
   - 20자 단위 분절 (한국어 최적화)
   - 시작/종료 시간 계산 (누적 duration 기반)
3. SRT 포맷으로 변환
4. SRT 파일 S3 업로드 (key: {job_id}/subtitles/subtitles.srt)
5. Asset 테이블 등록 (asset_type="subtitle")
6. JobStepExecution 완료 (progress 80%)

의존성: TTS(step4a) 완료 후 실행 (실제 오디오 길이 필요)
"""
```

### 32. step4d_bgm.py (BGM)

**파일**: `app/pipeline/steps/step4d_bgm.py`

```python
"""
Celery Task: bgm_task

Input: job_id
Flow:
1. VideoJob의 style에 따라 BGM 선택
   - assets/bgm/ 디렉토리에서 스타일별 BGM 파일 매칭
   - informative → calm_bgm.mp3
   - entertaining → upbeat_bgm.mp3
   - educational → neutral_bgm.mp3
   - news → news_bgm.mp3
2. 영상 전체 길이에 맞게 루프 처리
3. S3 업로드 (key: {job_id}/audio/bgm.mp3)
4. Asset 테이블 등록 (asset_type="bgm")
5. JobStepExecution 완료 (progress 82%)

include_bgm=False인 경우 → skip
"""
```

### 33. cost_tracker.py (비용 추적 + Guardrail)

**파일**: `app/services/cost_tracker.py`

```python
"""
API 호출별 비용을 실시간 추적하고 예산 초과를 방지.

class CostTracker:
    비용 단가 (설정에서 변경 가능):
    - Gemini 2.5 Flash: $0.15/1M input, $0.60/1M output
    - Gemini 2.5 Pro: $1.25/1M input, $10/1M output
    - GPT-4o: $2.50/1M input, $10/1M output
    - DALL-E 3 (1792x1024): $0.08/장
    - TTS-1-HD: $0.03/1,000자

    async def record_cost(job_id, step_name, provider, model, **usage) -> CostLog:
        - CostLog 레코드 생성
        - VideoJob.total_cost_usd 갱신

    async def check_budget(job_id) -> BudgetStatus:
        - 현재 누적 비용 vs cost_budget_usd
        - BudgetStatus: { remaining_usd, percent_used, degrade_level }

    async def get_degrade_level(job_id) -> int:
        - 0: 정상
        - 1: DALL-E 이미지 수 50% 감소
        - 2: Gemini Pro → Flash 다운그레이드
        - 3: 이미지 전부 text_overlay
        - 4: job 실패

    async def should_degrade_images(job_id, priority) -> bool:
        - 예산 상태 + 씬 priority로 degradation 판단

12분 영상 예상 비용:
    Gemini 대본: ~$0.05
    GPT-4o 검수: ~$0.03
    GPT-4o 정책 검수: ~$0.02
    DALL-E 이미지 8장: ~$0.64
    카드/차트 10장: $0
    TTS 2,500자: ~$0.08
    총 예상: ~$0.82
"""
```

### 34. artifact_registry.py (산출물 등록/조회/삭제)

**파일**: `app/storage/artifact_registry.py`

```python
"""
Job별 산출물 관리 (S3 + DB 연동).

class ArtifactRegistry:
    async def register(job_id, asset_type, scene_id, data, mime_type) -> Asset:
        - S3 업로드
        - Asset 테이블 등록
        - object_key 반환

    async def get_assets(job_id, asset_type=None) -> list[Asset]:
        - job의 산출물 목록 조회

    async def get_presigned_url(asset) -> str:
        - presigned URL 생성 (인증된 사용자만 접근)

    async def delete_job_assets(job_id, after_step=None) -> int:
        - job의 산출물 삭제 (retry from step 시 사용)
        - after_step 지정 시 해당 step 이후 산출물만 삭제

    async def cleanup_expired(ttl_hours) -> int:
        - TTL 초과 산출물 정리 (periodic task에서 호출)
"""
```

---

## 선행 조건
- Phase 4 완료 (FullScript가 S3에 존재해야 함)
- OpenAI API 키 유효 (TTS, DALL-E)
- assets/bgm/ 디렉토리에 BGM 파일 존재
- assets/fonts/ 디렉토리에 NanumGothic 폰트

## 완료 기준
- [ ] TTS — 씬별 나레이션 오디오 생성 + S3 업로드
- [ ] 이미지 — asset_type별 분기 처리 (DALL-E, quote_card, data_chart 등)
- [ ] 자막 — SRT 포맷 생성, 한국어 20자 분절
- [ ] BGM — 스타일별 선택 + 루프 처리
- [ ] CostTracker — 누적 비용 추적, degrade level 정상 동작
- [ ] ArtifactRegistry — S3 + DB 연동, presigned URL 발급
- [ ] 예산 초과 시 자동 degradation (text_overlay 대체 등)
