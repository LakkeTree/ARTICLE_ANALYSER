# WebProgram - Article Analyser Dashboard

Reflex 기반 웹 대시보드 애플리케이션입니다.

## 설치

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
# pip install -r ./requirements.txt #Linux/Mac

#unzip 설치
sudo apt install
sudo apt install unzip

# Reflex 초기화
reflex init
```

## 실행

```bash
# 가상환경 활성화 - 안했을시
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

#allowed Host 설정
#WebProgram/web/vite.config.js 파일 내 73번째 라인 'hmr: true,' 다음에 allowedHosts : ['본인아이디.web.ajousw.kr'],를 추가해준다.

# 기본 포트로 실행 (3000/8000)
reflex run

# 다른 포트로 실행
reflex run --frontend-port 3002 --backend-port 8002
```

브라우저에서 http://localhost:3000 (또는 지정한 포트) 접속

## 데이터 구조

- `res/rank/*.csv`: 날짜별 키워드 랭킹 데이터
- `res/summary/*.sum`: 날짜별 기사 요약 데이터

## 주요 기능

1. **Dashboard**: 최근 7일 데이터 카드, 라인/바 차트
2. **상세 순위**: 날짜별 상위 30개 키워드 테이블
3. **요약 기사**: 날짜별 기사 요약 (분류 필터, 페이지네이션)
