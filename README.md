# Article Analyser

경제 뉴스 기사를 분석하여 키워드 추출, 요약, 시각화를 제공하는 프로젝트입니다.

## 📋 프로젝트 구조

```
article_analyser/
├── Downloader/          # 뉴스 기사 다운로드 모듈
├── Tokenizer/           # 키워드 추출 및 토크나이징 모듈
├── Summarizer/          # 기사 요약 모듈
└── WebProgram/          # Reflex 기반 웹 대시보드
```

## 🚀 시작하기

### 사전 요구사항

- Python 3.10 이상
- Node.js (Reflex 웹 프로그램용)

### 설치 방법

1. **저장소 클론**
```bash
git clone <repository-url>
cd article_analyser
```

2. **각 모듈별 가상환경 생성 및 의존성 설치**

#### Downloader 모듈
```bash
cd Downloader
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
deactivate
cd ..
```

#### Tokenizer 모듈
```bash
cd Tokenizer
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
deactivate
cd ..
```

#### Summarizer 모듈
```bash
cd Summarizer
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
deactivate
cd ..
```

#### WebProgram 모듈
```bash
cd WebProgram
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
reflex init  # Reflex 초기화
deactivate
cd ..
```

### 디렉토리 구조 생성

각 모듈의 데이터 디렉토리를 생성합니다:

```bash
# Windows
mkdir Downloader\data
mkdir Summarizer\data
mkdir Tokenizer\data
mkdir WebProgram\WebProgram\res\rank
mkdir WebProgram\WebProgram\res\summary

# Linux/Mac
mkdir -p Downloader/data
mkdir -p Summarizer/data
mkdir -p Tokenizer/data
mkdir -p WebProgram/WebProgram/res/rank
mkdir -p WebProgram/WebProgram/res/summary
```

## 📖 사용 방법

### 1. Downloader - 기사 다운로드
```bash
cd Downloader
.venv\Scripts\activate
python main.py
deactivate
```

### 2. Tokenizer - 키워드 추출
```bash
cd Tokenizer
.venv\Scripts\activate
python main.py
deactivate
```

### 3. Summarizer - 기사 요약
```bash
cd Summarizer
.venv\Scripts\activate
python main.py
deactivate
```

### 4. WebProgram - 웹 대시보드 실행
```bash
cd WebProgram
.venv\Scripts\activate
reflex run
# 브라우저에서 http://localhost:3000 접속
```

다른 포트 사용 시:
```bash
reflex run --frontend-port 3002 --backend-port 8002
```

## 🎯 주요 기능

### WebProgram 대시보드

1. **Dashboard (메인)**
   - 최근 7일간의 데이터 카드 표시
   - 상위 4개 키워드 표시
   - 라인 차트: 상위 5개 키워드 추이
   - 바 차트: 날짜별 키워드 비교

2. **상세 순위 페이지**
   - 선택한 날짜의 상위 30개 키워드 테이블
   - 빈도수 차트

3. **요약 기사 페이지**
   - 선택한 날짜의 기사 요약 목록
   - 분류별 필터링
   - 페이지네이션 (20개씩 표시)

## 🛠️ 기술 스택

- **Backend**: Python 3.10+
- **Web Framework**: Reflex
- **Frontend**: React (Reflex 생성)
- **Data Visualization**: Recharts
- **Package Management**: Poetry (각 모듈)

## 📝 데이터 형식

### CSV 파일 (Tokenizer 출력)
```csv
word,count
금융,2509
대출,1253
은행,994
```

### 요약 파일 (.sum)
```
<분류>: 주식 시장
<요약>: 코스피가 롤러코스터 장세 끝에 장중 3,800선을 사상 처음으로 돌파...

<분류>: 보험
<요약>: 자동차보험 비교·추천 서비스 2.0이 고객 데이터 연동을 통해...
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🐛 문제 해결

### Reflex 실행 오류
- `reflex init`를 먼저 실행했는지 확인
- Node.js가 설치되어 있는지 확인
- 포트가 이미 사용 중이면 다른 포트 지정

### 가상환경 활성화 오류 (Windows)
```bash
# PowerShell에서 실행 정책 설정
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 데이터 파일이 없는 경우
- 각 모듈을 순서대로 실행하여 데이터 생성
- Downloader → Tokenizer → Summarizer → WebProgram

## 📧 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.
