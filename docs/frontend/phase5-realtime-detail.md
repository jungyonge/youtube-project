# Phase 5: 실시간 진행 + 상세

## 목표
SSE 기반 실시간 진행 표시, Job 상세 페이지(진행/대본/결과 탭), 액션 버튼(취소/승인/재시도/다운로드)을 구현한다.
백엔드 SSE 이벤트 포맷, 비디오 다운로드/재생 URL 전략, 대본 API를 확인/수정한다.

---

## 구현 항목

### 프론트엔드

#### 37. hooks/use-job-stream.ts (SSE + polling fallback)

#### 38. components/jobs/job-progress.tsx
```tsx
/**
 * 시각 요소:
 * 1. 가로 스텝퍼:
 *    완료=초록●, 진행중=파랑◐(pulse), 대기=회색○, 실패=빨강✕, 승인대기=노랑⏸
 *
 * 2. 프로그레스 바 (shimmer 애니메이션)
 *
 * 3. 상세 텍스트 + 경과 시간 카운터
 *
 * 4. 비용 뱃지: "$0.52 / $2.00"
 *    80%이상: yellow, 초과: red
 *
 * 5. 연결 상태: SSE=초록"실시간", Polling=노랑"폴링", 끊김=빨강
 */
```

#### 39. components/jobs/job-progress-steps.tsx
- Step별 테이블

#### 40. components/jobs/job-cost-badge.tsx

#### 41. components/jobs/job-actions.tsx (취소/재시도/다운로드)
```
버튼 표시 규칙 (상태 전이표 기반):

  const TERMINAL_STATES = ['completed', 'failed', 'cancelled', 'rejected'];
  const canCancel = !TERMINAL_STATES.includes(phase);
  const canApprove = phase === 'awaiting_approval';
  const canReject = phase === 'awaiting_approval';
  const canRetry = TERMINAL_STATES.includes(phase);
  const canDownload = phase === 'completed';

  retry 시 주의:
  - 새 job이 생성됨 (기존 job은 그대로 유지)
  - 응답: { job_id: "새-uuid", parent_job_id: "기존-uuid" }
  - navigate(`/jobs/${newJobId}`)로 새 job 상세로 이동
  - 기존 job 상세에는 "재시도본이 있습니다" 링크 표시

  모든 버튼에 mutation.isPending 동안 disabled + 스피너.
```

#### 42. hooks/use-job-actions.ts
```typescript
/**
 * useCancelJob(): mutation → POST /api/v1/videos/{jobId}/cancel
 * useRetryJob(): mutation → POST /api/v1/videos/{jobId}/retry
 * useApproveJob(): mutation → POST /api/v1/videos/{jobId}/approve
 * useRejectJob(): mutation → POST /api/v1/videos/{jobId}/reject
 *
 * ★ 모든 mutation의 onSuccess에 반드시:
 *   queryClient.invalidateQueries({ queryKey: ['jobs'] })
 *   queryClient.invalidateQueries({ queryKey: ['job', jobId] })
 *   queryClient.invalidateQueries({ queryKey: ['job-steps', jobId] })
 * 캐시 무효화를 안 하면 새로고침 전까지 대시보드/상세가 이전 상태로 남음.
 *
 * ★ 낙관적 업데이트(Optimistic Updates) 적용:
 *   cancel, approve, reject 등은 API 응답 전에 UI를 먼저 변경한다.
 *   체감 반응 속도를 0ms로 만들기 위함.
 *
 *   패턴:
 *   useCancelJob = useMutation({
 *     mutationFn: (jobId) => api.jobs.cancel(jobId),
 *     onMutate: async (jobId) => {
 *       await queryClient.cancelQueries({ queryKey: ['job', jobId] });
 *       const previous = queryClient.getQueryData(['job', jobId]);
 *       queryClient.setQueryData(['job', jobId], (old) => ({
 *         ...old, phase: 'cancelled', is_cancelled: true
 *       }));
 *       return { previous };
 *     },
 *     onError: (err, jobId, context) => {
 *       queryClient.setQueryData(['job', jobId], context.previous); // 롤백
 *       toast.error('취소에 실패했습니다');
 *     },
 *     onSettled: (_, __, jobId) => {
 *       queryClient.invalidateQueries({ queryKey: ['jobs'] });
 *       queryClient.invalidateQueries({ queryKey: ['job', jobId] });
 *     },
 *   });
 *
 *   approve, reject도 동일 패턴 적용.
 */
```

#### 43. components/jobs/job-detail-panel.tsx

#### 44. pages/job-detail-page.tsx (탭: 진행/대본/결과)

```
URL: /jobs/:jobId

┌─────────────────────────────────────────────────────┐
│  제목 | 상태 뱃지 | 비용 | 생성일 | 액션 버튼          │
├─────────────────────────────────────────────────────┤
│  실시간 진행 (job-progress.tsx)                       │
│  ● 추출 → ● 정규화 → ● 대본 → ◐ 검수 → ○ ...       │
│  [████████████████░░░░░░░] 67%                      │
│  "씬 5/16 이미지 생성 중..."                          │
│  $0.52 / $2.00                                      │
├─────────────────────────────────────────────────────┤
│  탭: [진행 상세] [대본] [결과]                         │
│                                                     │
│  진행 상세: 각 Step 실행 기록 테이블                    │
│  대본: 씬별 카드 + claim 뱃지 + 정책 플래그             │
│  결과: 비디오 플레이어 + 다운로드 + 유튜브 메타 복사      │
└─────────────────────────────────────────────────────┘

결과 탭 비디오 플레이어 구현 시 주의:

<video
  src={downloadUrl}
  controls
  preload="metadata"
  playsInline                          // iOS 인라인 재생 (전체화면 강제 방지)
  controlsList="nodownload"            // 브라우저 기본 다운로드 숨김 (커스텀 다운로드 버튼 사용)
  className="w-full rounded-lg"
/>

- iOS Safari: playsInline 필수, 없으면 전체화면으로 강제 전환됨
- 모바일 자동재생: autoPlay를 쓰려면 muted 필수 (브라우저 정책)
  → 우리 영상은 나레이션이 있으므로 autoPlay 사용하지 않음
- 다운로드는 별도 버튼 (GET /download 엔드포인트 경유)

비용 초과 실패 시 에러 UI 세분화:
  job.phase === "failed" 일 때, error_message를 파싱하여:
  - "budget_exceeded" → 일반 에러가 아닌 전용 UI 표시:
    "예산($2.00)을 초과하여 생성이 중단되었습니다.
     예산을 높여서 다시 시도하거나, 이미지 수를 줄여보세요."
    + [예산 높여서 재시도] 버튼 (retry with higher budget)
  - 그 외 에러 → 일반 에러 카드 + [재시도] 버튼
```

---

### 백엔드 수정

#### 45. SSE 이벤트 data 포맷 확인
```python
"""
프론트의 EventSource는 event.data를 JSON.parse한다.
백엔드 SSE가 보내는 각 이벤트가 아래 형태인지 확인:

event: progress
data: {"phase":"generating_assets","progress_percent":67,"current_step_detail":"씬 5/16 이미지 생성 중...","cost_usd":0.52}

event: completed
data: {"download_url":"https://...presigned...","thumbnail_url":"...","duration_sec":720,"total_cost":0.85}

event: approval_required
data: {"script_preview_url":"https://...presigned...","sensitivity_level":"high"}

event: failed
data: {"error_message":"DALL-E rate limit","last_completed_step":"review","can_retry":true}

event: cost_warning
data: {"current_cost":1.6,"budget":2.0,"message":"예산의 80%를 사용했습니다"}

event: cancelled
data: {}

주의:
- 각 이벤트에 'event:' 라인과 'data:' 라인이 모두 있어야 함
- 'data:' 값은 유효한 JSON이어야 함
- 이벤트 간 빈 줄(\n\n)으로 구분
- sse-starlette 사용 시 ServerSentEvent(data=json.dumps(...), event="progress")
"""
```

#### 46. [치명적] 비디오 다운로드/재생 URL 전략 확인
```python
"""
★ Presigned URL 만료 대응 (핵심):
  사용자가 완료 화면을 띄워둔 채 2시간 뒤 다운로드 클릭 시
  Presigned URL이 만료되어 403 에러 발생.

  해결: SSE completed 이벤트의 download_url을 직접 쓰지 않는다.
  대신 프론트는 항상 아래 엔드포인트를 통해 접근:

  GET /api/v1/videos/{job_id}/download
    → 호출 시점에 1시간짜리 신규 Presigned URL을 발급
    → 307 Redirect로 해당 URL로 보냄
    → 프론트: <a href="/api/v1/videos/{jobId}/download">다운로드</a>

  GET /api/v1/videos/{job_id}/thumbnail
    → 같은 방식으로 썸네일 Presigned URL 신규 발급 + redirect

  이 방식이면 URL 만료 걱정 없음.
  SSE의 download_url은 즉시 재생용으로만 사용하되,
  프론트에서 다운로드 버튼은 반드시 위 엔드포인트를 가리켜야 함.

★ MP4 스트리밍 재생 (Range Request 지원):
  프론트 결과 탭에서 <video src="...">로 15분 영상을 재생한다.
  사용자가 10분 지점으로 Seek하면 브라우저가 Range Request를 보낸다.

  확인 사항:
  1. S3 업로드 시 Content-Type을 "video/mp4"로 명시적 지정
  2. MinIO/S3는 기본적으로 Range Request(HTTP 206) 지원하므로
     별도 설정 불필요. 단, Presigned URL 방식이면 문제없음.
  3. 만약 백엔드가 프록시로 파일을 중계한다면(StreamingResponse),
     Range 헤더를 파싱하여 부분 응답 구현 필요 → 복잡하므로
     Presigned URL redirect 방식을 권장.
  4. [치명적] FFmpeg 인코딩 시 -movflags +faststart 플래그 필수:
     FFmpeg 기본 인코딩은 메타데이터(moov atom)를 파일 맨 끝에 기록한다.
     이 경우 수백MB 파일 다운로드가 100% 끝날 때까지
     브라우저가 영상을 1초도 재생할 수 없고 Seek도 불가능하다.
     -movflags +faststart를 추가하면 moov atom이 파일 앞으로 이동하여
     다운로드 시작 즉시 재생 + Seek이 가능해진다.

     백엔드 step5_assemble.py의 FFmpeg 옵션 확인:
       -c:v libx264 -preset medium -crf 23
       -c:a aac -b:a 192k
       -r 30 -s 1920x1080
       -movflags +faststart    ← 이 플래그가 반드시 있어야 함

     없으면 추가할 것.

  프론트:
  <video src={downloadUrl} controls preload="metadata" />
  downloadUrl은 Presigned URL (직접 S3/MinIO 접근)

★ MinIO CORS 설정:
  브라우저에서 <video>로 MinIO URL을 직접 재생하려면
  MinIO에도 CORS가 설정되어야 함.

  docker-compose 초기화 스크립트 또는 mc 커맨드:
    mc alias set myminio http://localhost:9000 minioadmin minioadmin
    mc cors set myminio/video-pipeline-outputs --allow-origin "http://localhost:5173"
    mc cors set myminio/video-pipeline-assets --allow-origin "http://localhost:5173"

  또는 MinIO 환경변수:
    MINIO_BROWSER_REDIRECT_URL=http://localhost:9001
    MINIO_CORS_ALLOW_ORIGIN=http://localhost:5173
"""
```

#### 47. GET /api/v1/videos/{job_id}/script 응답 확인
```python
"""
프론트 대본 탭과 승인 페이지에서 사용.
FullScript JSON을 직접 반환하거나, presigned URL로 반환하거나.

방법 1 (권장): 직접 JSON 반환
  GET /api/v1/videos/{job_id}/script → FullScript JSON body

방법 2: presigned URL 반환 후 프론트에서 fetch
  GET /api/v1/videos/{job_id}/script → { "url": "https://...presigned..." }
  프론트에서 해당 URL을 다시 fetch

방법 1이 프론트 구현이 간단함. 대본 JSON은 크기가 작으므로 직접 반환 권장.
"""
```
