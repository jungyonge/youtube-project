# 06. 영상 생성 (Job Create) 테스트 (단위)

## 목적
영상 생성 폼의 소스 관리, 폼 제출, 성공/에러 처리를 테스트합니다.

### 핵심 동작 (use-jobs.ts 기준)
- 성공 시: queryClient.invalidateQueries → `toast.success("영상 생성이 시작되었습니다.")` → `navigate(/jobs/{job_id})`
- 409 시: `toast.info("이미 동일한 요청이 있습니다.")` → navigate to existing job
- 기타 에러: `toast.error("영상 생성에 실패했습니다.")`

## 사전 조건
- 로그인 완료 상태

---

## 테스트 케이스 1: 최소 필수 정보로 영상 생성

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com / testpassword123 으로 로그인
2. 대시보드에서 영상 생성 폼에 다음을 입력:
   - 주제: "인공지능의 미래와 우리 삶의 변화에 대한 이야기"
   - 소스 URL: "https://example.com/ai-article" (기본 blog 타입)
   - 스타일: "정보 전달" (기본값 유지)
3. "영상 생성 시작" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - "영상 생성이 시작되었습니다." 토스트가 표시되는지
   - 작업 상세 페이지(/jobs/{jobId})로 자동 이동했는지
     (useCreateJob의 onSuccess: navigate(`/jobs/${data.job_id}`))
   - 작업 상태가 "대기 중" 또는 "콘텐츠 추출"인지
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- API 201 Created → 토스트 → 작업 상세 페이지로 이동

---

## 테스트 케이스 2: 소스 추가 및 삭제

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. browser_snapshot으로 소스 입력 영역 확인 — 기본 1개 소스
2. 기본 소스의 삭제 버튼(Trash2)이 **비활성화(disabled)** 상태인지 확인
   (fields.length <= 1이면 삭제 불가)
3. "소스 추가" 버튼(Plus 아이콘)을 클릭
4. browser_snapshot — 소스 2개 확인
5. 이제 첫 번째 소스의 삭제 버튼이 **활성화**되었는지 확인
6. 두 번째 소스의 타입 드롭다운에서 "유튜브"를 선택
7. 두 번째 소스 URL에 "https://youtube.com/watch?v=test" 입력
8. browser_snapshot으로 확인
9. 두 번째 소스의 삭제 버튼(Trash2)을 클릭
10. browser_snapshot — 소스가 다시 1개로 줄었는지 확인
11. 삭제 버튼이 다시 비활성화인지 확인
12. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 소스 최소 1개 유지 (삭제 비활성화)
- 추가/삭제 정상 동작

---

## 테스트 케이스 3: 소스 최대 10개 제한

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. "소스 추가" 버튼을 반복 클릭하여 소스를 10개까지 추가
2. 매번 browser_snapshot으로 소스 개수 확인
3. 10개에 도달했을 때:
   - "소스 추가" 버튼이 **사라졌는지** 확인
     (fields.length < 10 조건이 false이면 버튼 미렌더링)
4. 소스 하나를 삭제하여 9개로 만들기
5. "소스 추가" 버튼이 다시 나타나는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 10개 도달 시 추가 버튼 숨김
- 9개 이하로 내려가면 다시 표시

---

## 테스트 케이스 4: 소스 타입별 입력 UI 변경

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 소스 타입 드롭다운 확인 — 4가지 옵션:
   - "블로그" (blog)
   - "뉴스" (news)
   - "유튜브" (youtube)
   - "직접 입력" (custom_text)
2. 기본값 "블로그" → URL 입력 필드(Input, placeholder: "https://...") 확인
3. "뉴스"로 변경 → 여전히 URL 입력 필드인지 확인
4. "유튜브"로 변경 → 여전히 URL 입력 필드인지 확인
5. "직접 입력"(custom_text)으로 변경
6. browser_snapshot으로 확인:
   - URL 입력 필드가 **사라지고** Textarea가 나타나는지
   - placeholder: "텍스트를 직접 입력하세요..."
7. 텍스트 에어리어에 "직접 작성한 내용입니다." 입력
8. 다시 "블로그"로 변경하면 URL 입력 필드로 돌아가는지 확인
9. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- custom_text: Textarea, 그 외: Input(URL)

---

## 테스트 케이스 5: 고급 설정 변경 후 생성

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 주제: "React와 TypeScript를 활용한 웹 개발 튜토리얼" 입력
2. 소스 URL: "https://example.com/react-tutorial" 입력
3. 스타일: "튜토리얼" 선택
4. "고급 설정" 클릭하여 펼침
5. 다음 설정 변경:
   - 음성: "Nova (여성)" 선택
   - 배경 음악: OFF로 변경
   - 비용 예산: 3.0 입력
   - 자동 승인: OFF로 변경
   - 추가 지시사항: "초보자도 이해할 수 있는 쉬운 언어로 설명해주세요"
6. browser_snapshot으로 설정 상태 확인
7. "영상 생성 시작" 버튼 클릭
8. browser_snapshot으로 결과 확인
9. 작업 상세 페이지로 이동했는지, 토스트가 표시되는지 확인
10. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 모든 설정이 반영된 채로 생성 요청 성공

---

## 테스트 케이스 6: 일일 할당량 초과 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

참고: 기본 일일 할당량은 5건/일입니다.
axios 인터셉터에서 429 시 toast.error("요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요.")

1. Header의 할당량 배지를 먼저 확인: "오늘 N/5"
2. 영상 생성을 반복 시도하여 할당량(5건) 초과
3. 할당량 초과 시 browser_snapshot으로 확인:
   - "요청 제한을 초과했습니다." 토스트가 표시되는지
   - 또는 "Daily quota exceeded" 관련 메시지
   - Header의 배지가 "오늘 5/5" 형태이고 destructive 색상인지
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 429 Too Many Requests → 토스트 에러
- Header 배지 색상 변경

---

## 테스트 케이스 7: 생성 버튼 로딩 상태 (isPending)

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 주제: "테스트 영상 로딩 상태 확인" 입력
2. 소스 URL: "https://example.com/test" 입력
3. "영상 생성 시작" 버튼 클릭 직후 빠르게 browser_snapshot
4. 버튼 텍스트가 "생성 중..."으로 변경되었는지 확인
5. 버튼이 disabled 상태인지 확인 (중복 제출 방지)
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- isPending 중 "생성 중..." + disabled

---

## 테스트 케이스 8: custom_text 소스 빈 텍스트 제출 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 주제: "직접 입력 빈 텍스트 테스트입니다" 입력
2. 소스 타입을 "직접 입력"(custom_text)으로 변경
3. Textarea에 아무것도 입력하지 않음 (빈 상태)
4. "영상 생성 시작" 버튼 클릭
5. browser_snapshot으로 결과 확인
6. custom_text 소스에 텍스트가 비어있을 때:
   - "텍스트를 입력하세요" 또는 유사한 유효성 에러가 표시되는지
   - 또는 서버에서 400 에러가 반환되는지
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 빈 custom_text → 유효성 에러

---

## 테스트 케이스 9: 주제에 XSS/HTML 태그 입력 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 주제에 다음 입력: "<script>alert('xss')</script> AI 트렌드"
2. 소스 URL: "https://example.com/test"
3. "영상 생성 시작" 버튼 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - JavaScript alert가 실행되지 않는지
   - 작업이 생성되었다면, 상세 페이지에서 주제가 이스케이프 처리되어 표시되는지
   - DOM에 스크립트 태그가 실행 가능한 형태로 삽입되지 않는지
6. browser_console_messages로 에러 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- XSS 페이로드가 이스케이프 처리됨, 스크립트 실행 안 됨

---

## 테스트 케이스 10: 동일 소스 URL 중복 입력 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 주제: "중복 소스 URL 테스트 영상입니다" 입력
2. 첫 번째 소스 URL: "https://example.com/same-url"
3. "소스 추가" 클릭
4. 두 번째 소스 URL에도: "https://example.com/same-url" (동일 URL)
5. "영상 생성 시작" 클릭
6. browser_snapshot으로 결과 확인:
   - 중복 URL 경고가 표시되는지
   - 또는 정상 제출되는지 (서버의 normalize 단계에서 중복 제거)
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 중복 URL 처리 방식 확인 (클라이언트 경고 또는 서버 중복 제거)

---

## 테스트 케이스 11: 폼 작성 중 페이지 이탈 시 데이터 유실 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서 대시보드)

1. 주제에 긴 텍스트 입력: "시간 들여서 작성한 중요한 영상 주제입니다"
2. 소스를 3개 추가하고 URL 입력
3. "고급 설정" 펼쳐서 여러 옵션 변경
4. 제출하지 않고 Sidebar의 "내 영상" 클릭
5. browser_snapshot으로 /jobs 페이지 이동 확인
6. 다시 "대시보드" 클릭하여 돌아오기
7. browser_snapshot으로 확인:
   - 이전에 입력한 주제, 소스, 설정이 유지되는지
   - 또는 초기화되어 있는지
8. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 폼 데이터 유실 여부 확인 (UX 관점에서 중요한 검증 포인트)

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(06-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
