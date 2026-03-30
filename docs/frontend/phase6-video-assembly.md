# Phase 6: 영상 조립

## 목표
RenderManifest 기반 최종 영상 조립, Ken Burns 효과, FFmpeg 진행률 추적,
중간 산출물 S3 정리를 구현한다.

---

## 구현 항목

### 35. video_utils.py

**파일**: `app/utils/video_utils.py`
- MoviePy/FFmpeg 헬퍼 함수
- Ken Burns 효과 구현
- 전환 효과 적용

### 36. render_manifest.py 생성 로직

**파일**: `app/pipeline/models/render_manifest.py`

```python
class RenderManifest(BaseModel):
    """
    영상 조립기(step5)에 전달하는 최종 렌더 지시서.
    대본 모델과 렌더 모델을 분리하여 관심사를 격리.
    """
    job_id: str
    total_scenes: int
    resolution: str = "1920x1080"
    fps: int = 30
    codec: str = "libx264"
    crf: int = 23
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"

    scenes: list["RenderSceneInstruction"]
    bgm_object_key: str | None
    bgm_volume_db: float = -20.0
    subtitle_srt_key: str | None
    burn_subtitles: bool = True
    intro_template_key: str | None = None
    outro_template_key: str | None = None

class RenderSceneInstruction(BaseModel):
    scene_id: int
    audio_object_key: str
    audio_duration_sec: float
    image_object_key: str
    ken_burns_effect: Literal["zoom_in", "zoom_out", "pan_left", "pan_right"]
    transition_in: str | None
    transition_out: str | None
    silence_after_sec: float = 0.5
```

### 37. step5_assemble.py (sync worker task)

**파일**: `app/pipeline/steps/step5_assemble.py`

```python
"""
RenderManifest를 입력받아 최종 영상을 조립한다.
이 Step은 CPU 바운드이므로 render 큐의 sync worker task로 실행.
concurrency=1이므로 한 번에 한 영상만 렌더링.

@celery_app.task(queue='render', bind=True)
def assemble_video_task(self, ...):

조립 순서:
1. S3에서 모든 asset 다운로드 → 로컬 temp
2. MoviePy로 씬별 클립 생성
3. Ken Burns 효과 적용 (RenderSceneInstruction 기반)
4. 전환 효과 적용
5. 나레이션 오디오 합성
6. BGM 믹싱 (-20dB)
7. 자막 burn-in
8. 인트로/아웃트로
9. FFmpeg 최종 인코딩: H.264 1080p 30fps
10. 최종 MP4를 S3 업로드
11. 로컬 temp 즉시 삭제
12. 중간 산출물 S3 정리 (아래 참조)

FFmpeg 실시간 진행률 추적 (중요):
  MoviePy/FFmpeg가 동기적으로 렌더링하는 동안
  코드가 블로킹되어 Redis에 진행률을 업데이트할 수 없다.
  프론트에서 15분 동안 "렌더링 중..." 에서 멈추는 문제 발생.

  해결:
  - FFmpeg을 subprocess.Popen으로 직접 실행하고
    -progress pipe:1 옵션으로 진행 상황을 stdout으로 출력
  - 또는 MoviePy의 logger='bar' 대신 커스텀 proglog 콜백 연결
  - 별도 스레드에서 stdout을 읽으면서 10초마다 Redis PUBLISH
  - progress_percent 계산: (처리된_프레임 / 총_프레임) * 100

  구현 패턴:
    import subprocess, threading

    def run_ffmpeg_with_progress(cmd, job_id, total_duration_sec):
        proc = subprocess.Popen(
            cmd + ['-progress', 'pipe:1', '-nostats'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        def read_progress():
            current_time = 0
            for line in proc.stdout:
                line = line.decode().strip()
                if line.startswith('out_time_ms='):
                    current_time = int(line.split('=')[1]) / 1_000_000
                    percent = min(int(current_time / total_duration_sec * 100), 99)
                    # 10초마다 Redis PUBLISH
                    redis.publish(f'job:{job_id}:progress', json.dumps({
                        'phase': 'assembling_video',
                        'progress_percent': 80 + (percent * 0.2),  # 전체의 80~100% 구간
                        'current_step_detail': f'렌더링 {percent}% ({int(current_time)}초/{total_duration_sec}초)'
                    }))

        t = threading.Thread(target=read_progress, daemon=True)
        t.start()
        proc.wait()
        t.join(timeout=5)

중간 산출물 S3 정리 (스토리지 비용 최적화):
  최종 MP4가 S3에 성공적으로 업로드된 후,
  이 영상을 만드는 데 사용된 중간 산출물을 정리한다.

  즉시 삭제 대상:
  - tts_audio (씬별 mp3 파일 ~18개)
  - scene_image (씬별 이미지 파일 ~18개)
  - subtitle (SRT 파일)
  - bgm (선택된 BGM 파일)

  유지 대상:
  - video (최종 MP4) → output TTL(24시간) 후 삭제
  - thumbnail (썸네일) → output TTL 후 삭제
  - script JSON → output TTL 후 삭제

  구현:
  - Asset 테이블에서 해당 job_id의 중간 산출물 조회
  - S3 batch delete 실행
  - Asset 레코드의 is_deleted 플래그 업데이트
  - 삭제된 용량 로깅

  실패 시:
  - 중간 산출물 삭제 실패는 영상 생성 실패로 처리하지 않음
  - periodic_tasks의 cleanup에서 재시도
"""
```

### 38. Ken Burns 효과

- zoom_in, zoom_out, pan_left, pan_right 4종
- RenderSceneInstruction 기반 씬별 적용

---

## 선행 조건
- Phase 5 완료 (TTS, 이미지, 자막, BGM asset 생성 가능)

## 완료 기준
- [ ] video_utils.py 헬퍼 함수 동작
- [ ] RenderManifest + RenderSceneInstruction 모델 정의 완료
- [ ] step5_assemble.py sync worker task 동작
- [ ] Ken Burns 효과 4종 적용 동작
- [ ] 전환 효과 적용 동작
- [ ] BGM 믹싱 (-20dB) 동작
- [ ] 자막 burn-in 동작
- [ ] FFmpeg 진행률 10초마다 Redis PUBLISH 동작
- [ ] 최종 MP4 S3 업로드 동작
- [ ] 중간 산출물 S3 즉시 삭제 동작
- [ ] 로컬 temp 즉시 삭제 동작
