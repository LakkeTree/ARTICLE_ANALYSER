# Git Push 전 체크리스트

## ✅ 완료된 작업

### 1. .gitignore 업데이트
- [x] 데이터 디렉토리 제외
- [x] 가상환경 제외
- [x] 캐시 파일 제외
- [x] Reflex 생성 파일 제외
- [x] IDE 설정 파일 제외

### 2. 문서 작성
- [x] 루트 README.md (프로젝트 전체 설명)
- [x] WebProgram/README.md (웹 앱 설명)
- [x] 설치 가이드
- [x] 사용 방법

### 3. 설정 파일
- [x] WebProgram/requirements.txt
- [x] 각 모듈의 pyproject.toml 확인

### 4. 디렉토리 구조
- [x] 빈 디렉토리에 .gitkeep 추가
  - Downloader/data/.gitkeep
  - Tokenizer/data/.gitkeep
  - Summarizer/data/.gitkeep
  - WebProgram/WebProgram/res/rank/.gitkeep
  - WebProgram/WebProgram/res/summary/.gitkeep

### 5. 설치 스크립트
- [x] setup.bat (Windows)
- [x] setup.sh (Linux/Mac)

## 📝 Git 명령어

### 1. 변경사항 확인
```bash
git status
```

### 2. 파일 추가
```bash
# 모든 파일 추가
git add .

# 또는 개별 파일 추가
git add README.md
git add .gitignore
git add setup.bat
git add setup.sh
git add WebProgram/requirements.txt
git add WebProgram/README.md
git add Downloader/data/.gitkeep
git add Tokenizer/data/.gitkeep
git add Summarizer/data/.gitkeep
git add WebProgram/WebProgram/res/rank/.gitkeep
git add WebProgram/WebProgram/res/summary/.gitkeep
```

### 3. 커밋
```bash
git commit -m "docs: Add project documentation and setup scripts

- Add comprehensive README.md with installation guide
- Update .gitignore for data files and build artifacts
- Add requirements.txt for WebProgram
- Add setup scripts (setup.bat, setup.sh)
- Add .gitkeep files for empty directories
- Update WebProgram README"
```

### 4. GitHub에 푸시
```bash
# 원격 저장소 추가 (처음만)
git remote add origin https://github.com/your-username/article_analyser.git

# 푸시
git push -u origin main
```

## 🔍 푸시 전 확인사항

### 필수 확인
- [ ] `.env` 파일이 있다면 .gitignore에 포함되었는지 확인
- [ ] API 키나 비밀번호가 코드에 하드코딩되지 않았는지 확인
- [ ] 개인정보나 민감한 데이터가 포함되지 않았는지 확인
- [ ] 대용량 파일(.csv, .sum 등)이 제외되었는지 확인

### 권장 확인
- [ ] 모든 pyproject.toml 파일이 올바른지 확인
- [ ] README.md의 저장소 URL 업데이트
- [ ] LICENSE 파일 추가 (선택사항)

## 🚀 다른 PC에서 사용 시

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/article_analyser.git
cd article_analyser
```

### 2. 자동 설치 (권장)
```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

### 3. 수동 설치
README.md의 설치 가이드 참조

## 📌 주의사항

1. **데이터 파일**: CSV와 .sum 파일은 Git에 포함되지 않습니다. 각 모듈을 실행하여 생성해야 합니다.

2. **가상환경**: 각 모듈마다 별도의 가상환경이 생성됩니다.

3. **Node.js**: WebProgram 실행을 위해 Node.js가 필요합니다.

4. **포트 충돌**: Reflex 기본 포트(3000/8000)가 사용 중이면 다른 포트를 지정하세요.
