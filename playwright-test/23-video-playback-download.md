# 23. 비디오 재생 및 다운로드 테스트

## 목적
완료된 작업의 비디오 재생, 다운로드, presigned URL 처리,
상태별 결과 탭 표시를 검증합니다.

## 사전 조건
- 로그인 완료
- completed 상태의 작업 최소 1개 존재

---

## 테스트 케이스 1: 완료 Job → Result 탭 → `<video>` 요소 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 비디오 재생 테스트를 수행해줘:

(completed 상태의 작업 상세 페이지에서)

### Step 1: Result 탭 이동
1. "결과" 탭 클릭
2. browser_snapshot으로 결과 영역 캡처

### Step 2: video 요소 상세 검증
3. browser_evaluate로 video 요소 속성 확인:
   ```javascript
   const video = document.querySelector('video');
   if (!video) return { exists: false };

   return {
     exists: true,
     src: video.src,
     hasControls: video.hasAttribute('controls'),
     width: video.clientWidth,
     height: video.clientHeight,
     readyState: video.readyState,
     networkState: video.networkState,
     error: video.error ? { code: video.error.code, message: video.error.message } : null,
     // Presigned URL 파라미터 확인
     hasAmzSignature: video.src.includes('X-Amz-Signature'),
     hasAmzExpires: video.src.includes('X-Amz-Expires') || video.src.includes('Expires'),
     srcLength: video.src.length
   };
   ```
4. 확인 사항:
   - `<video>` 요소 존재
   - `controls` 속성 존재 (사용자가 재생/일시정지/볼륨 조절 가능)
   - `src`가 유효한 presigned URL (S3 서명 파라미터 포함)
   - 에러 없음 (`error: null`)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `<video controls>` 존재, 유효한 presigned URL, 에러 없음

---

## 테스트 케이스 2: 비디오 재생 시작 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 비디오 재생 테스트를 수행해줘:

(completed 작업의 "결과" 탭에서)

### Step 1: 비디오 재생 시도
1. browser_evaluate로 비디오 재생:
   ```javascript
   const video = document.querySelector('video');
   if (!video) return { error: 'video element not found' };

   // 재생 시도
   try {
     await video.play();
     // 0.5초 대기 후 상태 확인
     await new Promise(r => setTimeout(r, 500));
     return {
       playing: !video.paused,
       currentTime: video.currentTime,
       duration: video.duration,
       readyState: video.readyState,
       // readyState: 0=HAVE_NOTHING, 1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 3=HAVE_FUTURE_DATA, 4=HAVE_ENOUGH_DATA
       error: null
     };
   } catch (e) {
     return {
       playing: false,
       error: e.message,
       readyState: video.readyState
     };
   }
   ```
2. 확인 사항:
   - `playing: true` (재생 중)
   - `currentTime > 0` (재생 진행)
   - `duration > 0` (전체 길이 로드)
   - `readyState >= 2` (데이터 로드됨)

### Step 2: 일시정지
3. browser_evaluate로 일시정지:
   ```javascript
   const video = document.querySelector('video');
   video.pause();
   return { paused: video.paused, currentTime: video.currentTime };
   ```
4. `paused: true` 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 비디오 재생/일시정지 정상 동작
- ⚠️ 실제 비디오 파일이 MinIO에 존재해야 함

---

## 테스트 케이스 3: MP4 다운로드 링크 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 다운로드 테스트를 수행해줘:

(completed 작업의 "결과" 탭에서)

### Step 1: 다운로드 링크 확인
1. browser_snapshot으로 "MP4 파일 다운로드" 링크 확인
2. browser_evaluate로 링크 속성 검증:
   ```javascript
   const links = Array.from(document.querySelectorAll('a'));
   const downloadLink = links.find(a =>
     a.textContent.includes('MP4') || a.textContent.includes('다운로드')
   );

   if (!downloadLink) return { found: false };

   return {
     found: true,
     href: downloadLink.href,
     target: downloadLink.target,
     download: downloadLink.download,
     hasPresignedUrl: downloadLink.href.includes('X-Amz-Signature'),
     // 링크가 외부 S3 URL인지 내부 API URL인지
     isExternalUrl: !downloadLink.href.includes('localhost:5173')
   };
   ```

### Step 2: 다운로드 링크 유효성 검증
3. browser_evaluate로 링크 URL에 HEAD 요청:
   ```javascript
   const links = Array.from(document.querySelectorAll('a'));
   const downloadLink = links.find(a =>
     a.textContent.includes('MP4') || a.textContent.includes('다운로드')
   );
   if (!downloadLink) return { error: 'link not found' };

   try {
     const res = await fetch(downloadLink.href, { method: 'HEAD' });
     return {
       status: res.status,
       contentType: res.headers.get('Content-Type'),
       contentLength: res.headers.get('Content-Length'),
       contentDisposition: res.headers.get('Content-Disposition')
     };
   } catch (e) {
     return { error: e.message };
   }
   ```
4. 확인 사항:
   - status: 200
   - Content-Type: video/mp4 또는 application/octet-stream
   - Content-Length > 0

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 다운로드 링크가 유효한 presigned URL
- HEAD 요청 200 응답 + 적절한 Content-Type

---

## 테스트 케이스 4: 미완료 Job → Result 탭 빈 상태

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

다양한 비완료 상태에서 "결과" 탭 표시를 확인합니다:

### Step 1: 진행 중인 작업 (queued / extracting 등)
1. 진행 중인 작업의 상세 페이지
2. "결과" 탭 클릭
3. browser_snapshot 확인:
   - "영상이 아직 생성되지 않았습니다." 메시지
   - `<video>` 요소 없음
   - 다운로드 링크 없음

### Step 2: 실패한 작업 (failed)
4. failed 작업의 상세 페이지
5. "결과" 탭 클릭
6. browser_snapshot 확인:
   - AlertTriangle 아이콘 + "생성 실패" 메시지
   - error_message 표시
   - `<video>` 요소 없음

### Step 3: 취소된 작업 (cancelled)
7. cancelled 작업의 상세 페이지
8. "결과" 탭 클릭
9. browser_snapshot 확인:
   - "영상이 아직 생성되지 않았습니다." 또는 취소 관련 메시지

### Step 4: 승인 대기 작업 (awaiting_approval)
10. awaiting_approval 작업의 "결과" 탭
11. "영상이 아직 생성되지 않았습니다." 메시지 확인

각 상태별 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 비완료 상태 → 비디오 플레이어 미표시 + 적절한 안내 메시지

---

## 테스트 케이스 5: Presigned URL 포맷 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 presigned URL 테스트를 수행해줘:

### Step 1: 비디오 URL 구조 분석
1. completed 작업의 상세 페이지 → "결과" 탭
2. browser_evaluate로 presigned URL 파싱:
   ```javascript
   const video = document.querySelector('video');
   if (!video || !video.src) return { error: 'no video src' };

   const url = new URL(video.src);
   return {
     protocol: url.protocol,
     hostname: url.hostname,
     port: url.port,
     pathname: url.pathname,
     // S3 presigned URL 파라미터
     params: Object.fromEntries(url.searchParams.entries()),
     hasSignature: url.searchParams.has('X-Amz-Signature') || url.searchParams.has('Signature'),
     hasExpires: url.searchParams.has('X-Amz-Expires') || url.searchParams.has('Expires'),
     hasCredential: url.searchParams.has('X-Amz-Credential'),
     hasDate: url.searchParams.has('X-Amz-Date'),
     // MinIO 로컬 확인
     isLocalMinio: url.hostname === 'localhost' && url.port === '9000'
   };
   ```

### Step 2: URL 유효성 확인
3. S3/MinIO presigned URL의 필수 파라미터 확인:
   - X-Amz-Algorithm (예: AWS4-HMAC-SHA256)
   - X-Amz-Credential
   - X-Amz-Date
   - X-Amz-Expires
   - X-Amz-SignedHeaders
   - X-Amz-Signature
4. 또는 Query String Authentication V2 형태:
   - AWSAccessKeyId
   - Expires
   - Signature

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Presigned URL에 S3 서명 파라미터 모두 포함
- MinIO 로컬 환경에서는 localhost:9000 호스트

---

## 테스트 케이스 6: usePlaybackUrl 30분 캐시 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 캐시 테스트를 수행해줘:

### Step 1: 첫 번째 playback URL 호출
1. completed 작업의 상세 페이지
2. "결과" 탭 클릭
3. browser_evaluate로 현재 video src 기록:
   ```javascript
   const video = document.querySelector('video');
   return { url1: video?.src };
   ```

### Step 2: 탭 전환 후 재접근
4. "진행 상세" 탭 클릭
5. "결과" 탭 다시 클릭
6. browser_evaluate로 video src 다시 확인:
   ```javascript
   const video = document.querySelector('video');
   return { url2: video?.src };
   ```

### Step 3: URL 비교
7. url1과 url2가 동일한지 확인:
   - 동일 → React Query 캐시 동작 (staleTime: 30분)
   - 다름 → 매번 새 presigned URL 발급 (캐시 미동작)

### Step 4: 페이지 이탈 후 재접근
8. /dashboard로 이동 후 다시 작업 상세 → "결과" 탭
9. url3 기록
10. url1과 url3 비교:
    - 동일 → 캐시 유지
    - 다름 → 페이지 이탈 시 캐시 무효화

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 같은 페이지 내 탭 전환: 캐시된 URL 재사용 (API 재호출 없음)
- 페이지 이탈 후 재접근: 캐시 상태에 따라 다름

---

## 테스트 케이스 7: 비디오 로딩 실패 시 에러 상태

### 프롬프트

```
Playwright MCP를 사용하여 다음 비디오 에러 테스트를 수행해줘:

### Step 1: 비디오 로딩 에러 시뮬레이션
1. completed 작업의 "결과" 탭에서
2. browser_evaluate로 video src를 잘못된 URL로 변경:
   ```javascript
   const video = document.querySelector('video');
   if (!video) return { error: 'no video element' };

   const originalSrc = video.src;

   // 에러 이벤트 리스너 추가
   return new Promise((resolve) => {
     video.onerror = () => {
       resolve({
         errorOccurred: true,
         errorCode: video.error?.code,
         errorMessage: video.error?.message,
         networkState: video.networkState
       });
     };

     // 잘못된 URL 설정
     video.src = 'http://localhost:9000/non-existent-bucket/non-existent-file.mp4';
     video.load();

     // 타임아웃
     setTimeout(() => {
       resolve({
         errorOccurred: false,
         note: 'No error event within 5 seconds',
         networkState: video.networkState
       });
     }, 5000);
   });
   ```

### Step 2: 에러 UI 확인
3. browser_snapshot으로 비디오 영역 확인:
   - 에러 표시 또는 기본 비디오 플레이어 에러 UI
   - 사용자에게 "비디오를 불러올 수 없습니다" 같은 메시지 표시 여부

### Step 3: 원래 URL 복원
4. 페이지 새로고침으로 원래 상태 복원

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 비디오 로딩 실패 시 브라우저 기본 에러 UI 또는 커스텀 에러 메시지
- ⚠️ FE에 video error 핸들링이 구현되어 있지 않을 수 있음 (확인 필요)

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(23-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
