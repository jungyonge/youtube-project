# 17. 접근성 (Accessibility) 테스트

## 목적
키보드 네비게이션, 포커스 관리, ARIA 속성, 색상 대비, 스크린 리더 호환성 등
WCAG 2.1 기준의 접근성을 E2E로 테스트합니다.

---

## 테스트 케이스 1: 로그인 폼 키보드 네비게이션

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. browser_press_key로 Tab 키를 순차적으로 입력
3. 각 Tab에서 포커스가 이동하는 순서 확인:
   - 이메일 필드 → 비밀번호 필드 → 로그인 버튼 → 회원가입 링크
4. browser_snapshot으로 각 포커스 상태에서 시각적 포커스 표시 확인:
   - focus-visible ring/outline이 보이는지
5. 이메일/비밀번호 입력 후 Tab → Enter로 로그인 버튼 활성화 확인
6. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Tab 순서가 논리적이고 시각적 포커스 표시 존재

---

## 테스트 케이스 2: 회원가입 폼 키보드 네비게이션

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. Tab 키로 포커스 이동 순서 확인:
   - 이메일 → 비밀번호 → 비밀번호 확인 → 회원가입 버튼 → 로그인 링크
3. Shift+Tab으로 역순 이동 확인
4. 각 필드에서 포커스 링이 보이는지 확인
5. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 순방향/역방향 Tab 네비게이션 정상

---

## 테스트 케이스 3: 폼 에러 메시지 접근성

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. http://localhost:5173/register 접속
2. 빈 폼 제출 → 에러 메시지 발생
3. browser_snapshot으로 에러 메시지 확인
4. 다음 접근성 요소 확인:
   - 에러 메시지에 role="alert" 또는 aria-live="polite" 속성이 있는지
   - 에러가 있는 필드에 aria-invalid="true"가 설정되는지
   - 에러 메시지가 aria-describedby로 입력 필드와 연결되어 있는지
   - 포커스가 첫 번째 에러 필드로 이동하는지
5. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 에러 메시지가 스크린 리더에서 접근 가능

---

## 테스트 케이스 4: 대시보드 Sidebar 키보드 접근성

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. 로그인 후 대시보드
2. Tab 키로 Sidebar 내 요소 순회:
   - "대시보드" 링크 → "내 영상" 링크 → (관리자면 "관리" 링크) → 테마 토글 → 로그아웃 버튼
3. Enter 키로 네비게이션 링크 활성화 확인
4. Sidebar 접기/펼치기 버튼이 키보드로 접근 가능한지 확인
5. 테마 토글 버튼이 Space 또는 Enter로 동작하는지 확인
6. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 모든 Sidebar 요소가 키보드로 접근/조작 가능

---

## 테스트 케이스 5: 영상 생성 폼 접근성

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. 로그인 후 대시보드의 영상 생성 폼
2. 다음 접근성 요소 확인:
   - 주제 Textarea에 적절한 label이 연결되어 있는지 (htmlFor/id 또는 aria-label)
   - 소스 URL 필드에 label이 있는지
   - 스타일 선택 버튼들이 radio group으로 구성되었는지 (role="radiogroup" 또는 유사)
   - 현재 선택된 스타일에 aria-pressed="true" 또는 aria-selected="true"가 있는지
   - "고급 설정" 토글에 aria-expanded 속성이 있는지
   - 슬라이더에 aria-valuemin, aria-valuemax, aria-valuenow 속성이 있는지
   - 스위치(자막, BGM, 자동 승인)에 role="switch"와 aria-checked가 있는지
3. Tab 순서가 논리적인지 확인
4. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 모든 폼 요소에 적절한 ARIA 속성

---

## 테스트 케이스 6: 모달/다이얼로그 포커스 트랩

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

(awaiting_approval 상태의 승인 페이지에서)

1. "거부" 버튼 클릭 → 거부 다이얼로그 열림
2. browser_snapshot으로 다이얼로그 확인
3. 다음 접근성 요소 확인:
   - 다이얼로그에 role="dialog" 또는 role="alertdialog" 속성이 있는지
   - aria-modal="true"가 설정되어 있는지
   - 다이얼로그 열림 시 포커스가 다이얼로그 내부로 이동하는지
4. Tab 키로 포커스가 다이얼로그 내부에서만 순환하는지 확인 (포커스 트랩):
   - Textarea → "취소" 버튼 → "거부 확인" 버튼 → (다시 Textarea로 순환)
5. Escape 키로 다이얼로그가 닫히는지 확인
6. 다이얼로그 닫힘 후 포커스가 원래 "거부" 버튼으로 돌아가는지 확인
7. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 포커스 트랩 동작, Escape 닫기, 포커스 복원

---

## 테스트 케이스 7: 토스트 알림 접근성

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. 로그인 성공 시 "로그인 성공" 토스트 발생
2. browser_snapshot으로 토스트 영역 확인
3. 다음 접근성 요소 확인:
   - 토스트 컨테이너에 role="status" 또는 aria-live="polite"가 있는지
   - 에러 토스트에는 role="alert"가 있는지
   - 토스트가 스크린 리더에 의해 자동으로 읽히는지 (aria-live)
   - 토스트가 일정 시간 후 자동 사라지는지 (auto-dismiss)
4. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 토스트가 aria-live 영역을 통해 스크린 리더에 전달

---

## 테스트 케이스 8: 작업 목록 카드 키보드 접근

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. /jobs 페이지에서 작업 카드들 확인
2. Tab 키로 카드 간 포커스 이동이 가능한지 확인
3. Enter 키로 카드 클릭(상세 이동)이 가능한지 확인
4. 카드에 적절한 role 속성이 있는지:
   - role="link" 또는 role="button"
   - 또는 <a> 태그로 감싸져 있는지
5. 카드에 aria-label 또는 적절한 텍스트 컨텐츠가 있는지
6. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 카드가 키보드로 접근/활성화 가능

---

## 테스트 케이스 9: 색상 대비 및 다크 모드 접근성

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

### 라이트 모드
1. 로그인 후 대시보드
2. browser_snapshot으로 텍스트 가시성 확인
3. 주요 텍스트 요소가 배경 대비 충분히 구분되는지 육안 확인:
   - 제목 텍스트 (진한 색)
   - 본문 텍스트 (회색 계열)
   - 에러 메시지 (빨간색)
   - 성공 메시지 (초록색)

### 다크 모드
4. 테마 토글 → 다크 모드 전환
5. browser_snapshot으로 다크 모드 확인
6. 다크 배경에서 텍스트가 충분히 밝은 색인지 확인:
   - 주요 텍스트가 여전히 읽기 쉬운지
   - Badge 색상이 다크 배경과 충분히 구분되는지
   - 입력 필드 테두리가 보이는지
7. 라이트 모드로 복원

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 라이트/다크 모두에서 충분한 색상 대비

---

## 테스트 케이스 10: 파이프라인 진행 상태 접근성

### 프롬프트

```
Playwright MCP를 사용하여 다음 접근성 테스트를 수행해줘:

1. 작업 상세 페이지의 파이프라인 인디케이터 확인
2. 다음 접근성 요소 확인:
   - 진행률 바에 role="progressbar"가 있는지
   - aria-valuenow, aria-valuemin(0), aria-valuemax(100) 속성이 있는지
   - aria-label로 "진행률 N%" 같은 설명이 있는지
   - 각 스텝의 색상 외에 텍스트/아이콘으로도 상태를 구분할 수 있는지
     (색맹 사용자를 위해 색상만으로 정보 전달하지 않는지)
3. SSE 연결 상태 배지의 아이콘 + 텍스트 확인:
   - 색상뿐 아니라 텍스트("실시간"/"폴링"/"끊김")로도 상태 전달
4. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 진행률 바에 ARIA 속성, 색상 외 대체 정보 제공

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(17-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
