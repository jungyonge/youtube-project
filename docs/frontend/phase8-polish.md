# Phase 8: 마무리

## 목표
다크모드, 반응형, 에러 상태, 로딩 스켈레톤, ErrorBoundary 등 전체 품질을 다듬는다.
백엔드 에러 응답 일관성을 확인하고, docker-compose에 프론트엔드 서비스를 추가한다.

---

## 구현 항목

### 프론트엔드

#### 63. 다크모드 전체 검증
- shadcn/ui는 기본 다크모드 지원
- 커스텀 컴포넌트의 `dark:` 클래스 확인

#### 64. 반응형 전체 검증
- 모바일: 사이드바 → 하단 탭, 폼/목록 단일 컬럼
- 태블릿: 사이드바 접힘

#### 65. 에러 상태 UI
- 빈 목록: "아직 생성한 영상이 없습니다" + CTA 버튼
- 네트워크 에러: retry 버튼이 있는 에러 카드
- 404: "영상을 찾을 수 없습니다"

#### 66. 로딩 스켈레톤
- job-list: 카드 스켈레톤 3개
- job-detail: 프로그레스 바 스켈레톤
- admin-table: 행 스켈레톤

#### 67. ErrorBoundary 래핑 (각 페이지)

#### 68. README.md

---

### 백엔드 수정

#### 69. 백엔드 에러 응답 일관성 확인
```python
"""
프론트 axios interceptor가 에러를 파싱하려면
백엔드 에러 응답이 일관된 형태여야 함:

{
  "detail": "에러 메시지 (한글)"
}

또는 validation error:
{
  "detail": [
    {
      "loc": ["body", "topic"],
      "msg": "주제를 입력해주세요",
      "type": "value_error"
    }
  ]
}

FastAPI 기본 HTTPException은 이 형태를 따르지만,
커스텀 에러 핸들러가 있으면 형태가 다를 수 있으니 확인.

특히:
- 401: { "detail": "인증이 필요합니다" }
- 403: { "detail": "권한이 없습니다" }
- 404: { "detail": "영상을 찾을 수 없습니다" }
- 409: { "detail": "이미 처리된 요청입니다", "job_id": "..." }
- 429: { "detail": "요청 제한을 초과했습니다" }
"""
```

#### 70. docker-compose.yml에 프론트엔드 서비스 추가 (선택)
```yaml
"""
개발 환경 + 프로덕션 환경 모두 대응.

  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - api

Dockerfile.dev (개발용):
  FROM node:20-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm install
  COPY . .
  CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

Dockerfile (프로덕션 - Multi-stage Build):
  # Stage 1: 빌드
  FROM node:20-alpine AS builder
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci
  COPY . .
  RUN npm run build

  # Stage 2: Nginx로 서빙
  FROM nginx:alpine
  COPY --from=builder /app/dist /usr/share/nginx/html
  COPY nginx.conf /etc/nginx/conf.d/default.conf
  EXPOSE 80
  CMD ["nginx", "-g", "daemon off;"]

nginx.conf:
  server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback (React Router)
    location / {
      try_files $uri $uri/ /index.html;
    }

    # API 프록시 (프로덕션)
    location /api/ {
      proxy_pass http://api:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE 프록시 (buffering 끄기 필수)
    location ~* /api/v1/videos/.*/stream {
      proxy_pass http://api:8000;
      proxy_set_header Host $host;
      proxy_buffering off;          # SSE 스트리밍 필수
      proxy_cache off;
      proxy_read_timeout 86400s;    # 긴 연결 유지
    }

    # 정적 자산 캐싱
    location ~* \.(js|css|png|jpg|svg|ico|woff2)$ {
      expires 1y;
      add_header Cache-Control "public, immutable";
    }
  }
"""
```
