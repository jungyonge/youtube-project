# Phase 6: 영상 조립

## 목표
생성된 모든 에셋(오디오, 이미지, 자막, BGM)을 조합하여
최종 MP4 영상을 생성한다. CPU 바운드 작업이므로 sync worker에서 실행.

---

## 구현 항목

### 35. video_utils.py

**파일**: `app/utils/video_utils.py`

```python
"""
영상 처리 유틸리티 함수 모음.

def apply_ken_burns(image_clip, effect, duration) -> VideoClip:
    Ken Burns 효과 적용.
    - zoom_in: 100% → 120% 서서히 확대
    - zoom_out: 120% → 100% 서서히 축소
    - pan_left: 우→좌 패닝
    - pan_right: 좌→우 패닝

def apply_transition(clip, transition_type, duration=0.5) -> VideoClip:
    전환 효과 적용.
    - fade_in / fade_out
    - crossfade
    - slide_left / slide_right

def create_scene_clip(image_path, audio_path, duration, ken_burns, silence_after) -> VideoClip:
    이미지 + 오디오 → 씬 클립 생성.
    - 이미지를 duration만큼 표시
    - 오디오 합성
    - Ken Burns 효과 적용
    - silence_after만큼 무음 추가

def mix_bgm(main_audio, bgm_path, bgm_volume_db=-20) -> AudioClip:
    나레이션 + BGM 믹싱.
    - BGM을 영상 길이에 맞게 루프
    - 지정된 볼륨으로 믹싱

def burn_subtitles(video_clip, srt_path, font_path=None) -> VideoClip:
    자막 burn-in.
    - SRT 파싱
    - 한글 폰트 적용
    - 화면 하단 중앙 배치
    - 반투명 배경 박스

def encode_final(video_clip, output_path, codec, crf, fps, audio_codec, audio_bitrate):
    FFmpeg 최종 인코딩.
    - H.264 1080p 30fps
    - AAC 192kbps
    - CRF 23
"""
```

### 36. RenderManifest 생성 로직

**파일**: `app/pipeline/models/render_manifest.py`

```python
class RenderSceneInstruction(BaseModel):
    scene_id: int
    audio_object_key: str
    audio_duration_sec: float
    image_object_key: str
    ken_burns_effect: Literal["zoom_in", "zoom_out", "pan_left", "pan_right"]
    transition_in: str | None
    transition_out: str | None
    silence_after_sec: float = 0.5

class RenderManifest(BaseModel):
    job_id: str
    total_scenes: int
    resolution: str = "1920x1080"
    fps: int = 30
    codec: str = "libx264"
    crf: int = 23
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    scenes: list[RenderSceneInstruction]
    bgm_object_key: str | None
    bgm_volume_db: float = -20.0
    subtitle_srt_key: str | None
    burn_subtitles: bool = True
    intro_template_key: str | None = None
    outro_template_key: str | None = None
```

**RenderManifest 생성 함수** (orchestrator 또는 별도 task):
```python
"""
FullScript + Asset 목록 → RenderManifest 변환.

1. 각 씬에 대해:
   - tts_audio Asset의 object_key → audio_object_key
   - scene_image Asset의 object_key → image_object_key
   - TTS 실측 duration → audio_duration_sec
   - Ken Burns 효과 자동 할당 (씬별 순환: zoom_in → zoom_out → pan_left → ...)
   - 전환 효과 매핑
2. BGM Asset의 object_key → bgm_object_key
3. 자막 Asset의 object_key → subtitle_srt_key
4. RenderManifest JSON을 S3에 저장
"""
```

### 37. step5_assemble.py (영상 조립 — sync worker)

**파일**: `app/pipeline/steps/step5_assemble.py`

```python
"""
Celery Task: assemble_task
⚠️ CPU 바운드 — sync worker task로 실행 (async 아님)

Input: job_id
Flow:
1. S3에서 RenderManifest 로드
2. S3에서 모든 asset 다운로드 → 로컬 temp 디렉토리
   - {TEMP_DIR}/{job_id}/images/
   - {TEMP_DIR}/{job_id}/audio/
   - {TEMP_DIR}/{job_id}/subtitles/
3. 씬별 클립 생성:
   - create_scene_clip(image, audio, duration, ken_burns, silence)
   - apply_transition(clip, transition)
4. 인트로 템플릿 적용 (있으면)
5. 전체 씬 연결 (concatenate)
6. 아웃트로 템플릿 적용 (있으면)
7. BGM 믹싱: mix_bgm(main_audio, bgm, volume_db)
8. 자막 burn-in: burn_subtitles(video, srt, font)
9. FFmpeg 최종 인코딩:
   encode_final(video, output_path, codec="libx264", crf=23, fps=30)
10. 최종 MP4를 S3 업로드
    - key: {job_id}/output/final.mp4
11. 썸네일 생성 (첫 프레임 또는 DALL-E 썸네일)
    - key: {job_id}/output/thumbnail.jpg
12. Asset 테이블 등록 (asset_type="video", "thumbnail")
13. VideoJob 업데이트:
    - output_video_key, output_thumbnail_key
    - total_duration_sec, generation_time_sec
    - phase = "completed"
    - completed_at = now
14. 로컬 temp 디렉토리 즉시 삭제
15. SSE "completed" 이벤트 전송
    { download_url, thumbnail_url, duration_sec, total_cost }
16. JobStepExecution 완료 (progress 100%)

에러 처리:
- MoviePy/FFmpeg 에러 → 상세 로그 + step 실패
- 디스크 공간 부족 → 사전 체크 + 에러 처리
- 로컬 temp는 성공/실패 관계없이 finally에서 삭제
"""
```

### 38. Ken Burns 효과

`video_utils.py`의 `apply_ken_burns` 함수에서 구현:

```python
"""
정적 이미지에 동적 카메라 효과를 부여하여 영상의 단조로움을 방지.

4가지 효과:
1. zoom_in: 이미지 중앙에서 서서히 확대 (100% → 120%)
2. zoom_out: 확대된 상태에서 서서히 축소 (120% → 100%)
3. pan_left: 이미지를 우측에서 좌측으로 패닝
4. pan_right: 이미지를 좌측에서 우측으로 패닝

구현:
- MoviePy의 resize + crop 조합
- 프레임별 위치/크기 계산 (linear interpolation)
- 1920x1080 기준, 패닝은 120% 크기 이미지에서 crop

씬별 자동 할당:
- 순환 패턴: zoom_in → pan_right → zoom_out → pan_left → ...
- 연속된 씬에 같은 효과 반복 방지
"""
```

---

## 선행 조건
- Phase 5 완료 (TTS, 이미지, 자막, BGM 에셋이 S3에 존재)
- FFmpeg 설치 (worker 컨테이너)
- 한글 폰트 설치 (자막 burn-in용)

## 완료 기준
- [ ] `video_utils.py` — Ken Burns, 전환 효과, BGM 믹싱, 자막 burn-in 동작
- [ ] RenderManifest 생성 — FullScript + Assets → 렌더 지시서 변환
- [ ] `step5_assemble.py` — 전체 에셋 조립 → MP4 생성 + S3 업로드
- [ ] 최종 영상: H.264, 1080p, 30fps, AAC 192kbps
- [ ] 썸네일 생성 + S3 업로드
- [ ] 로컬 temp 파일 정리 확인
- [ ] VideoJob 상태 "completed" + presigned download URL 발급
