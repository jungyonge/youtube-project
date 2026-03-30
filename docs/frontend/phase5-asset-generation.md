# Phase 5: 자산 생성

## 목표
TTS 음성, 이미지(DALL-E + 다양한 카드/차트), 자막, BGM 생성과
비용 추적/가드레일, 산출물 등록 시스템을 구현한다.

---

## 구현 항목

### 29. step4a_tts.py + retry

**파일**: `app/pipeline/steps/step4a_tts.py`
- ChatGPT TTS API 호출 (tts-1-hd)
- 씬별 나레이션 → 음성 파일 생성
- S3 업로드 + Asset 테이블 등록
- tenacity retry 적용

### 30. step4b_images.py (다양한 asset 생성)

**파일**: `app/pipeline/steps/step4b_images.py`

```python
"""
SceneAssetPlan의 asset_type에 따라 분기:

- "generated_image": DALL-E 3 API 호출 (기존)
- "quote_card": Pillow + 템플릿으로 인용문 카드 생성
    - assets/templates/quote_card.json 기반
    - 배경색, 폰트, 레이아웃 자동 적용
- "data_chart": matplotlib로 차트 이미지 생성
    - template_data에서 데이터 파싱
    - 한글 폰트 적용 (NanumGothic)
- "timeline_card": Pillow + 템플릿으로 타임라인 카드
- "title_card": Pillow로 제목 카드
- "web_capture": Playwright screenshot (원본 URL)
- "text_overlay": Pillow로 키워드 강조 화면
- "split_screen": Pillow로 좌/우 비교 이미지 합성

모든 결과는 1920x1080으로 리사이즈.
생성된 이미지는 S3 업로드 후 Asset 테이블에 등록.
"""
```

### 31. step4c_subtitles.py

**파일**: `app/pipeline/steps/step4c_subtitles.py`
- SRT 자막 생성
- subtitle_chunks (20자 단위) 기반
- S3 업로드 + Asset 등록

### 32. step4d_bgm.py

**파일**: `app/pipeline/steps/step4d_bgm.py`
- BGM 선택 및 처리
- S3 업로드 + Asset 등록

### 33. cost_tracker.py (비용 추적 + guardrail)

**파일**: `app/services/cost_tracker.py`

```python
"""
API 호출별 비용을 실시간 추적하고 예산 초과를 방지.

비용 단가 (2026년 3월 기준, 설정에서 변경 가능):
- Gemini 2.5 Flash: ~$0.15/1M input, ~$0.60/1M output
- Gemini 2.5 Pro: ~$1.25/1M input, ~$10/1M output
- GPT-4o: ~$2.50/1M input, ~$10/1M output
- DALL-E 3 (1792x1024): ~$0.08/장
- TTS-1-HD: ~$0.03/1,000자

12분 영상 예상 비용:
- Gemini 대본 생성: ~$0.05
- GPT-4o 검수: ~$0.03
- GPT-4o 정책 검수: ~$0.02
- DALL-E 이미지 8장: ~$0.64
- 카드/차트 10장: $0 (로컬 생성)
- TTS 2,500자: ~$0.08
- 총 예상: ~$0.82

예산 초과 시 자동 Degrade:
1단계: DALL-E 이미지 수 50% 감소 (나머지 text_overlay)
2단계: Gemini Pro → Flash 다운그레이드
3단계: 이미지 전부 text_overlay
4단계: job 실패 + 사용자 알림
"""
```

### 34. artifact_registry.py (산출물 S3 등록/조회)

**파일**: `app/storage/artifact_registry.py`
- job별 산출물 등록/조회/삭제
- Asset 테이블과 S3 연동

### 파이프라인 모델 (Pydantic)

**파일**: `app/pipeline/models/assets.py`

```python
class AudioAsset(BaseModel):
    ...

class ImageAsset(BaseModel):
    ...

class SceneAssetPlan(BaseModel):
    ...
```

---

## 선행 조건
- Phase 4 완료 (FullScript 생성 가능)

## 완료 기준
- [ ] TTS 음성 생성 + S3 업로드 동작
- [ ] DALL-E 이미지 생성 동작
- [ ] quote_card (Pillow + 템플릿) 생성 동작
- [ ] data_chart (matplotlib) 생성 동작
- [ ] timeline_card, title_card, text_overlay, split_screen 생성 동작
- [ ] web_capture (Playwright screenshot) 동작
- [ ] 모든 이미지 1920x1080 리사이즈 동작
- [ ] SRT 자막 생성 동작
- [ ] BGM 선택 및 처리 동작
- [ ] cost_tracker 비용 기록 동작
- [ ] 예산 초과 시 자동 Degrade (4단계) 동작
- [ ] artifact_registry S3 등록/조회 동작
