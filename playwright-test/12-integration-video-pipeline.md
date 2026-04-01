# 12. 통합 테스트: 영상 생성 파이프라인 전체 플로우

## 목적
로그인 → 영상 생성 → 파이프라인 진행 → 승인 → 완료까지의 전체 E2E 플로우를 테스트합니다.

---

## 통합 시나리오 1: 자동 승인 모드 — 영상 생성 전체 플로우

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘.
각 단계마다 browser_snapshot으로 상태를 확인하고, 실패 시 해당 단계에서 중단해줘:

### Step 1: 로그인
1. browser_navigate로 http://localhost:5173/login 에 접속
2. test@example.com / testpassword123 으로 로그인
3. 대시보드 진입 확인

### Step 2: Header 할당량 확인
4. Header의 할당량 배지: "오늘 N/5" 확인 (N 기록)

### Step 3: 영상 생성 (자동 승인 ON)
5. 주제 입력: "2024년 AI 기술 트렌드 총정리 - 생성형 AI부터 에이전트까지"
6. 소스 URL: "https://example.com/ai-trends-2024"
7. 스타일: "정보 전달" (기본값)
8. "영상 생성 시작" 클릭
9. browser_snapshot — 결과 확인:
   - "영상 생성이 시작되었습니다." 토스트
   - 작업 상세 페이지(/jobs/{jobId})로 자동 이동

### Step 4: 작업 상세 초기 상태
10. 9단계 파이프라인 인디케이터가 보이는지 확인
11. 상태 Badge 확인 (queued / extracting)
12. SSE 연결 상태 배지: "실시간" 또는 "폴링" 확인
13. 비용 배지: "$0.00 / $2.00" (기본 예산)

### Step 5: 파이프라인 진행 모니터링
14. 10초 간격으로 browser_snapshot 3회:
    - 진행률 바의 width % 변화 확인
    - 현재 단계 텍스트 변화 확인 (추출 → 정규화 → ...)
    - 파이프라인 인디케이터에서 초록색(완료) 스텝 수 증가 확인
    - 비용 누적 변화 확인
15. "진행 상세" 탭 클릭하여 단계별 상태 테이블 확인:
    - completed된 스텝에 CheckCircle + 소요 시간 + 비용 표시
    - running 스텝에 Loader2(회전) 표시

### Step 6: 자동 승인 확인
16. 자동 승인이므로 awaiting_approval에서 멈추지 않고 진행되는지 확인

### Step 7: 최종 결과 확인
17. 충분한 시간 후 browser_snapshot으로 최종 상태 확인:
    - completed: "완료" Badge + "다운로드" 버튼 + "결과" 탭에 비디오 플레이어
    - failed: "실패" Badge + 에러 메시지
    - 아직 진행 중: 현재 단계 정보

### Step 8: Header 할당량 변화
18. Header 할당량 배지가 "오늘 (N+1)/5"로 변경되었는지 확인

각 단계의 결과를 상세하게 리포트 형태로 정리해줘.
파이프라인 단계 전환이 관찰되면 기록해줘:
추출 → 정규화 → 근거 추출 → 대본 생성 → 대본 검수 → 정책 검토 → (자동 승인) → TTS/이미지 → BGM → 자막 → 조립

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 3 | 작업 생성 성공 |
| 4 | 상세 페이지 초기 상태 |
| 5 | 실시간 진행률 업데이트 |
| 6 | 승인 단계 자동 통과 |
| 7 | 파이프라인 완료 또는 진행 중 |
| 8 | 할당량 +1 반영 |

---

## 통합 시나리오 2: 수동 승인 모드 — 대본 검토 후 승인

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 로그인 후 자동 승인 OFF로 영상 생성
1. 로그인 → 대시보드
2. 주제: "비트코인 반감기가 시장에 미치는 영향 분석"
3. 소스 URL: "https://example.com/bitcoin-halving"
4. 스타일: "오피니언" 선택
5. "고급 설정" 펼치기
6. **"자동 승인" 스위치 OFF** (안내 문구 표시 확인)
7. 비용 예산: $5.00
8. "영상 생성 시작" 클릭 → 상세 페이지 이동

### Step 2: 파이프라인 진행 → 승인 대기
9. 파이프라인이 진행되는 것을 관찰
10. browser_wait_for 또는 반복 snapshot으로 "승인 대기" 상태 대기 (최대 5분)
11. "승인 대기" 도달 확인:
    - Badge: "승인 대기" (bg-yellow-100)
    - 파이프라인 인디케이터 "승인" 스텝: 노란색 깜빡임
    - "대본 승인이 필요합니다" 토스트가 표시되었는지
    - "승인" + "거부" 버튼이 JobActions에 표시되는지

### Step 3: 승인 페이지에서 대본 검토
12. browser_navigate로 /jobs/{jobId}/approval 에 접속
    (⚠️ /approve가 아니라 /approval)
13. ScriptPreview 확인:
    - PolicyFlagAlert (민감도 Badge 포함)
    - 대본 제목/부제
    - 씬 카드들 (나레이션, 근거 배지, 정책 플래그)
14. 하단 액션: "거부", "수정 요청", "승인하고 생성 시작"

### Step 4: 승인
15. "승인하고 생성 시작" 버튼 클릭
16. "대본이 승인되었습니다." 토스트 확인
17. 작업 상태 변화 확인: awaiting_approval → generating_assets 등

### Step 5: 승인 후 파이프라인 재개 확인
18. 파이프라인 인디케이터에서 "에셋" 스텝이 활성화(파란색)되는지
19. "대본" 탭에서 승인된 대본 내용 확인 가능한지
20. "진행 상세" 탭에서 이전 단계들이 completed, 현재 단계가 running인지

각 단계의 결과를 리포트 형태로 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 1 | 자동 승인 OFF 설정 확인 |
| 2 | awaiting_approval에서 일시 정지 |
| 3 | 승인 페이지에서 대본 확인 |
| 4 | 승인 → TTS 단계부터 재개 |
| 5 | 에셋 생성 진행 |

---

## 통합 시나리오 3: 수동 승인 모드 — 대본 거부 후 재시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 자동 승인 OFF로 영상 생성 → 승인 대기까지 진행
(시나리오 2의 Step 1~2와 동일)

### Step 2: 승인 페이지에서 거부
1. /jobs/{jobId}/approval 접속
2. "거부" 버튼 클릭 → 다이얼로그 열림
3. 거부 사유: "영양 관련 수치가 부정확하여 재작성이 필요합니다"
4. "거부 확인" 클릭
5. "대본이 거부되었습니다." 토스트 확인
6. 작업 상태 "거부됨" (rejected) 확인

### Step 3: 거부 후 작업 상세 상태
7. 작업 상세 페이지에서:
   - Badge: "거부됨" (bg-red-100)
   - "재시도" 버튼이 보이는지 확인
   - "진행 상세" 탭에서 중단 지점 확인

### Step 4: 재시도
8. "재시도" 버튼 클릭
9. "재시도 작업이 생성되었습니다." 토스트 확인
10. ⚠️ **BE 동작**: 새 Job 생성이 아니라 **같은 Job**의 phase를 `running`으로 업데이트
11. 같은 작업 상세 페이지에 머무는지 확인
12. browser_evaluate로 attempt_count 증가 확인:
    ```javascript
    const data = JSON.parse(localStorage.getItem('auth-storage'));
    const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
      headers: { 'Authorization': 'Bearer ' + data.state.token }
    });
    const job = await res.json();
    return { phase: job.phase, attempt_count: job.attempt_count };
    ```
13. phase: "running", attempt_count: 2 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 거부 처리 |
| 3 | rejected 상태 + 재시도 버튼 |
| 4 | ⚠️ 같은 Job 업데이트 (BE는 새 Job 미생성), attempt_count +1 |

---

## 통합 시나리오 4: 영상 생성 중 취소

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 영상 생성
1. 로그인 → 주제: "취소 테스트용 영상" → 생성

### Step 2: 진행 중 취소
2. 작업 상세에서 상태 확인 (queued/extracting 등)
3. "취소" 버튼 클릭
4. 낙관적 업데이트로 즉시 "취소됨" Badge 표시 확인
5. "작업이 취소되었습니다." 토스트 확인

### Step 3: 취소 후 UI 상태
6. "취소" 버튼 사라짐 확인
7. "재시도" 버튼 나타남 확인
8. 파이프라인 인디케이터: 진행된 스텝은 초록, 나머지는 회색

### Step 4: 대시보드 복귀 확인
9. "대시보드" 뒤로가기 클릭
10. 목록에서 해당 작업이 "취소됨" Badge로 표시 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 취소 성공 |
| 3 | UI 상태 업데이트 |
| 4 | 목록에서 취소 상태 확인 |

---

## 통합 시나리오 5: 수정 요청 플로우

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 자동 승인 OFF → 승인 대기까지 진행

### Step 2: 승인 페이지에서 수정 요청
1. /jobs/{jobId}/approval 접속
2. "수정 요청" 버튼 클릭 → 다이얼로그
3. 지시사항 비어있을 때 "수정 요청 확인" 버튼 disabled 확인
4. 지시사항: "3번 씬의 투자 예측 표현을 완화해주세요" 입력
5. "수정 요청 확인" 클릭
6. useRetryJob(from_step: "review") 호출 확인
7. "재시도 작업이 생성되었습니다." 토스트
8. 새 작업 상세 페이지 이동 확인

### Step 3: 새 작업 확인
9. parent_job_id 링크가 표시되는지
10. 파이프라인이 review 단계부터 재시작되는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 수정 요청 → retry(from_step: "review") |
| 3 | 새 작업에서 review부터 재시작 |

---

## 통합 시나리오 6: 파이프라인 실패 후 재시도 플로우

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 잘못된 소스로 영상 생성 (실패 유도)
1. 로그인 → 대시보드
2. 주제: "실패 테스트 - 존재하지 않는 소스 URL"
3. 소스 URL: "https://this-domain-does-not-exist-at-all-12345.com/article"
4. "영상 생성 시작" 클릭

### Step 2: 파이프라인 실패 관찰
5. 작업 상세 페이지에서 파이프라인 진행 관찰
6. 추출 단계(extracting)에서 실패 가능성 높음
7. browser_snapshot으로 실패 상태 확인 (최대 2분 대기):
   - Badge: "실패" (bg-red-100)
   - 파이프라인 인디케이터: 실패 스텝 빨간색 (bg-red-500)
   - "진행 상세" 탭: failed 스텝에 XCircle + error_message
   - "결과" 탭: AlertTriangle + "생성 실패" 메시지

### Step 3: 실패 후 재시도
8. "재시도" 버튼 확인 (canRetry: phase가 terminal)
9. "재시도" 클릭
10. "재시도 작업이 생성되었습니다." 토스트 확인
11. ⚠️ **BE 동작**: 같은 Job의 phase → `running`, attempt_count +1
12. 같은 작업 상세 페이지에 머무는지 확인
13. browser_evaluate로 확인:
    ```javascript
    const data = JSON.parse(localStorage.getItem('auth-storage'));
    const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
      headers: { 'Authorization': 'Bearer ' + data.state.token }
    });
    const job = await res.json();
    return { phase: job.phase, attempt_count: job.attempt_count };
    ```
14. 파이프라인이 extract 단계부터 재시작되는지 확인

각 단계의 결과를 리포트 형태로 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 추출 실패 → failed 상태 |
| 3 | ⚠️ 같은 Job 업데이트 (새 Job 미생성), attempt_count +1, extract부터 재시작 |

---

## 통합 시나리오 7: 작업 상세에서 승인 페이지 왕복 네비게이션

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 자동 승인 OFF 영상 생성 → 승인 대기
(시나리오 2의 Step 1~2와 동일하게 awaiting_approval까지 진행)

### Step 2: 작업 상세 → 승인 페이지 → 작업 상세 왕복
1. 작업 상세 페이지에서 "승인" 또는 승인 관련 링크 확인
2. 승인 페이지(/jobs/{jobId}/approval)로 이동
3. 대본 내용 확인
4. "상세로 돌아가기" 클릭 → /jobs/{jobId} 복귀 확인
5. 다시 승인 페이지로 이동
6. 다시 상세로 돌아가기

### Step 3: 승인 페이지에서 승인
7. 승인 페이지에서 "승인하고 생성 시작" 클릭
8. 작업 상세 페이지 또는 대시보드로 이동 확인
9. 상태가 변경되었는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 상세 ↔ 승인 왕복 네비게이션 정상 |
| 3 | 승인 후 상태 반영 |

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(12-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
