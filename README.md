# 쫄병코인 (Jjolbyeong Coin)

대장(Boss)이 쫄병(Minion)에게 코인을 지급하고, 쫄병은 대장마켓 구매·빗토코인 투자를 하는 웹 서비스.
기획 상세는 [쫄병코인_기획서.md](쫄병코인_기획서.md) 참고.

## 스택
- 프론트엔드: Vue 3 + TypeScript + Composition API + Vite + Tailwind CSS
- 백엔드: FastAPI (Python 3.14) + SQLAlchemy + Alembic
- DB: PostgreSQL 15
- 실시간: SSE (Server-Sent Events)

## 폴더 구조
```
쫄병코인/
├─ 쫄병코인_기획서.md      # 기획서
├─ backend/                # FastAPI
│  ├─ app/
│  │  ├─ core/             # 설정, DB 연결
│  │  ├─ models/           # SQLAlchemy 모델
│  │  ├─ events/           # SSE 이벤트 버스(pub/sub)
│  │  ├─ services/         # 코인 등 도메인 로직
│  │  ├─ api/              # 라우터 (stream, demo)
│  │  └─ main.py           # 엔트리포인트
│  ├─ alembic/             # 마이그레이션
│  ├─ .env                 # 시크릿(커밋 금지)
│  └─ requirements.txt
└─ frontend/               # Vue
   └─ src/
      ├─ api/              # 백엔드 호출
      ├─ composables/      # useCoinStream (SSE 구독)
      └─ App.vue           # SSE 데모 화면
```

## 실행 방법

### 1) 백엔드
```bash
cd backend
# 최초 1회: 가상환경 + 의존성
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
# DB 마이그레이션 (테이블 생성)
./.venv/Scripts/alembic.exe upgrade head
# 서버 실행 (http://127.0.0.1:8000)
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```
- 헬스체크: http://127.0.0.1:8000/api/health → `{"status":"ok","db":true}`
- API 문서(Swagger): http://127.0.0.1:8000/docs

### 2) 프론트엔드
```bash
cd frontend
npm install        # 최초 1회
npm run dev        # http://localhost:5173
```
Vite dev 서버가 `/api`를 백엔드(8000)로 프록시합니다. **백엔드를 먼저 켜세요.**

## 현재 구현 상태 (PoC)
- ✅ DB 연결 + 전체 테이블 스키마(Alembic)
- ✅ SSE 이벤트 버스 + `/api/stream` 구독
- ✅ 대장 코인 지급 → 쫄병 화면 실시간 반영 (새로고침 불필요)
- ✅ 모바일 우선 데모 화면

> `/api/demo/*` 는 인증 없이 동작하는 PoC용 임시 API입니다.
> 다음 단계에서 JWT 인증·가입/승인·대장마켓·빗토코인으로 확장합니다.
