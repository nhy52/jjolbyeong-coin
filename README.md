# 🪙 쫄병코인 (Jjolbyeong Coin)

> **칭찬 스티커의 디지털 버전.** 대장(Boss)이 쫄병(Minion)에게 코인을 지급하면,
> 쫄병 화면에 **새로고침 없이 실시간으로** 코인이 쌓입니다. 쌓은 코인으로 대장마켓에서 상품을 사거나 빗토코인에 투자할 수 있어요.

![Vue](https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169e1?logo=postgresql&logoColor=white)
![SSE](https://img.shields.io/badge/Realtime-SSE-ff6b5b)

---

## ✨ 이게 뭔가요?

부모–자녀, 사장–직원, 팀장–팀원, 커플·친구처럼 **소규모 그룹**에서 쓰는 보상 포인트 서비스입니다.

- **코인 = 칭찬/보상 포인트.** 실제 화폐가 아니라 대장이 그룹 안에서 무한히 발행할 수 있는 포인트예요.
- **대장이 지급하면 쫄병 화면에 실시간 반영.** 코인이 뒤집히며 튀어오르고 숫자가 카운트업됩니다. (SSE)
- **대장마켓** — 대장이 상품(예: "아이스크림 쿠폰")을 등록하면 쫄병이 코인으로 구매. 신규 상품·주문은 SSE로 실시간 반영.
- **상품 신청** — 쫄병이 "이거 마켓에 올려주세요"라고 대장에게 신청하면, 대장이 승인 시 그 내용으로 상품이 자동 등록.
- **빗토코인** — 5초마다 오르내리는 투자 상품으로 재미 요소. *(개발 예정)*

---

## 🎮 데모 계정으로 바로 체험하기

아래 순서로 서버를 띄운 뒤([시작하기](#-시작하기)), 두 계정으로 각각 로그인해 보세요.
대장 계정에서 코인을 지급하면 쫄병 계정 화면에 실시간으로 쌓이는 걸 볼 수 있습니다.

| 역할 | 이메일 | 비밀번호 | 설명 |
|------|--------|----------|------|
| 👑 **대장** | `boss@jjolcoin.app` | `demo1234` | 쫄병 승인 · 코인 지급 · 그룹 관리 |
| 🧒 **쫄병** | `minion@jjolcoin.app` | `demo1234` | 코인 지갑(시작 잔액 480) |

> 그룹 초대 코드: **`DEMO24`** — 직접 새 쫄병을 가입시켜 볼 때 사용하세요.
>
> 데모 계정은 `backend/seed_demo.py`로 생성됩니다. DB를 초기화했다면 이 스크립트를 다시 실행하면 계정이 복구됩니다.

**추천 체험 방법:** 브라우저 창 2개(또는 시크릿 창)를 나란히 띄워 한쪽은 대장, 한쪽은 쫄병으로 로그인 → 대장 화면에서 지급 → 쫄병 화면 숫자가 실시간으로 올라가는 걸 확인.

---

## 🧩 주요 기능

- **JWT 인증** — 대장/쫄병 회원가입, 로그인, 토큰 자동 갱신
- **초대 코드 기반 그룹** — 대장이 가입하면 그룹 + 초대 코드 자동 발급, 쫄병은 코드로 참여
- **가입 승인 플로우** — 쫄병 자가가입(`pending`) → 대장이 승인(`active`)
- **역할별 화면 분리** — 로그인 정보(role)에 따라 화면·하단 탭 메뉴가 완전히 달라짐
  - 쫄병 탭: `홈(코인 지갑)` · `대장마켓` · `빗토코인` · `내정보`
  - 대장 탭: `홈(초대코드·현황)` · `대장마켓` · `관리자` · `내정보`
- **실시간 코인 지급** — 대장이 지급하면 쫄병 화면에 SSE로 즉시 반영(새로고침 불필요)
- **대장마켓** — 대장 상품 등록/수정/삭제·이미지 업로드, 쫄병 구매(코인 차감)·주문 수령완료 처리, 신상품·주문 SSE 실시간 반영
- **상품 신청(쫄병 → 대장)** — 쫄병이 갖고 싶은 상품(이름·희망가·사유·참고 이미지/링크)을 신청 → 대장이 승인하면 마켓에 자동 등록, 거절 시 사유 전달. 신청/결과 SSE 실시간 반영
- **코인 원장(Ledger)** — 모든 코인 변동을 거래 내역으로 기록해 잔액 검증 가능
- **모바일 우선 UI** — 하단 탭 네비게이션 + 카드 레이아웃

---

## 🛠 기술 스택

| 영역 | 스택 |
|------|------|
| 프론트엔드 | Vue 3 · TypeScript · Vite · Vue Router · Pinia · Tailwind CSS |
| 백엔드 | FastAPI (Python 3.14) · SQLAlchemy · Alembic |
| 인증 | JWT (access/refresh) · bcrypt |
| 실시간 | SSE (Server-Sent Events, `sse-starlette`) |
| DB | PostgreSQL 15 |

---

## 🚀 시작하기

**사전 준비:** PostgreSQL 15 (로컬 `localhost:5432`, DB명 `jjolbyeong_coin`), Python 3.14, Node.js

### 1) 백엔드

```bash
cd backend

# 최초 1회: 가상환경 + 의존성
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# 환경변수 준비 (DB 접속정보·JWT 시크릿)
cp .env.example .env   # 값을 채워주세요

# DB 마이그레이션 (테이블 생성)
./.venv/Scripts/alembic.exe upgrade head

# 데모 계정 생성 (대장/쫄병)
./.venv/Scripts/python.exe seed_demo.py

# 서버 실행 (http://127.0.0.1:8000)
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

- 헬스체크: <http://127.0.0.1:8000/api/health> → `{"status":"ok","db":true}`
- API 문서(Swagger): <http://127.0.0.1:8000/docs>

### 2) 프론트엔드

```bash
cd frontend
npm install          # 최초 1회
npm run dev          # http://localhost:5173
```

Vite dev 서버가 `/api`를 백엔드(8000)로 프록시합니다. **백엔드를 먼저 켜세요.**

---

## 📁 프로젝트 구조

```
쫄병코인/
├─ 쫄병코인_기획서.md          # 상세 기획서
├─ backend/                    # FastAPI
│  ├─ app/
│  │  ├─ core/                 # 설정, DB, 보안(JWT/해싱), 인증 의존성
│  │  ├─ models/               # SQLAlchemy 모델
│  │  ├─ events/               # SSE 이벤트 버스(pub/sub)
│  │  ├─ services/             # auth · coin · market 도메인 로직
│  │  ├─ api/                  # auth · admin · market · stream · demo 라우터
│  │  └─ main.py               # 엔트리포인트
│  ├─ alembic/                 # 마이그레이션
│  └─ seed_demo.py             # 데모 계정 시드
└─ frontend/                   # Vue
   └─ src/
      ├─ api/                  # 백엔드 호출 (auth, admin, market)
      ├─ stores/               # Pinia (auth)
      ├─ router/               # 라우트 + 역할 가드
      ├─ layouts/              # AppShell (역할별 탭바)
      ├─ composables/          # useCoinStream · useMarketStream (SSE 구독)
      └─ views/                # 로그인·가입 / 쫄병 / 대장 화면
```

---

## 📌 구현 현황

- [x] DB 스키마 + 마이그레이션 (Alembic)
- [x] SSE 이벤트 버스 + 실시간 코인 반영
- [x] JWT 인증 (대장/쫄병 가입, 로그인, 토큰 갱신)
- [x] 초대 코드 그룹 + 쫄병 승인 플로우
- [x] 역할별 화면/메뉴 분리 (라우트 가드)
- [x] 대장 관리자 페이지 (쫄병 승인·코인 지급)
- [x] 대장마켓 (상품 CRUD·이미지 업로드·구매·주문 수령완료·SSE)
- [x] 상품 신청 (쫄병 신청 → 대장 승인 시 자동 등록 / 거절 사유)
- [ ] 빗토코인 (실시간 시세·투자)
- [ ] 코인 내역 타임라인, 통계 대시보드

자세한 설계는 [쫄병코인_기획서.md](쫄병코인_기획서.md)를 참고하세요.
