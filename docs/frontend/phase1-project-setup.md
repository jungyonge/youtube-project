# Phase 1: 프로젝트 셋업

## 목표
Vite + React + TypeScript 프로젝트를 생성하고, Tailwind CSS, shadcn/ui 등 기본 인프라를 구축한다.
백엔드 CORS 설정과 MinIO Presigned URL 내부/외부망 분리를 함께 처리한다.

---

## 구현 항목

### 프론트엔드

#### 1. Vite + React + TypeScript 프로젝트 생성
- `frontend/` 디렉토리에 프로젝트 생성

#### 2. Tailwind CSS + PostCSS 설정

#### 3. shadcn/ui 초기화
- 필요 컴포넌트: button, input, card, dialog, select, switch, slider,
  badge, tabs, table, textarea, separator, dropdown-menu, avatar,
  alert, tooltip, label, form, sonner

#### 4. 디렉토리 구조 생성

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
│
├── public/
│   └── favicon.svg
│
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── config/
    ├── lib/
    ├── stores/
    ├── hooks/
    ├── types/
    ├── components/
    │   ├── ui/
    │   ├── layout/
    │   ├── auth/
    │   ├── jobs/
    │   ├── approval/
    │   └── admin/
    └── pages/
```

#### 5. .env.example
```
VITE_API_BASE_URL=http://localhost:8000
```

#### 6. vite.config.ts
- proxy: `/api` → `http://localhost:8000`

#### 7. src/config/env.ts

#### 8. src/index.css
- Tailwind directives + 다크모드 변수

---

### 백엔드 수정

#### 9. CORSMiddleware 추가 (없으면)
**파일**: `app/main.py`
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 10. [치명적] MinIO Presigned URL 내부/외부망 분리
**파일**: `object_store.py`
```python
"""
백엔드(Docker 내부)는 MinIO에 http://minio:9000 으로 접근한다.
그래서 생성되는 Presigned URL도 http://minio:9000/... 이 된다.

문제: 브라우저는 사용자 PC에서 실행되므로 'minio:9000' 호스트를
찾을 수 없어 영상 재생/다운로드가 100% 실패한다.
(ERR_NAME_NOT_RESOLVED)

해결: .env에 S3_PUBLIC_URL 환경변수를 추가하고,
클라이언트에 반환하는 URL은 public URL로 치환한다.

.env 추가:
  S3_ENDPOINT_URL=http://minio:9000        # 백엔드 내부 통신용
  S3_PUBLIC_URL=http://localhost:9000       # 브라우저 접근용 (프로덕션은 실제 도메인)

object_store.py 수정:
  def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
      url = self.client.generate_presigned_url(...)  # http://minio:9000/...
      # 내부 URL을 외부 URL로 치환
      if settings.s3_public_url:
          url = url.replace(settings.s3_endpoint_url, settings.s3_public_url)
      return url

config.py에 추가:
  s3_public_url: str = "http://localhost:9000"
"""
```
