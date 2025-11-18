# Ward Security System

<p align="center">
  <img src="assets/ward.png" alt="Ward Security System" width="200"/>
</p>

[![CI/CD](https://github.com/yamonco/ward/workflows/CI%2FCD/badge.svg)](https://github.com/yamonco/ward/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://img.shields.io/docker/pulls/yamonco/ward.svg)](https://hub.docker.com/r/yamonco/ward)

**Ward**는 특정 폴더에 제약을 거는 심플한 보안 서비스입니다. 파일 시스템 접근을 제어하고 안전한 개발 환경을 제공합니다.

## 🚀 주요 기능

- **디렉토리 접근 제어**: 특정 폴더에 대한 보안 정책 설정
- **명령어 화이트리스트/블랙리스트**: 허용/금지 명령어 관리
- **AI 협업 기능**: AI 코파일트와의 안전한 작업 지원
- **실시간 감사 로깅**: 모든 작업 내역 기록
- **Docker 지원**: 컨테이너 환경에서의 쉬운 배포
- **Python CLI**: 파이썬 기반 명령줄 인터페이스

## 📦 설치

### UV 사용 (권장)
```bash
uv tool install --from git+https://github.com/yamonco/ward.git ward

# 또는 직접 실행
uvx --from git+https://github.com/yamonco/ward.git ward-cli status
```

### Docker 사용
```bash
docker pull yamonco/ward:latest
docker run -it -v $(pwd):/workspace yamonco/ward:latest
```

### 직접 다운로드
```bash
wget https://github.com/yamonco/ward/releases/latest/download/ward-bash.tar.gz
tar -xzf ward-bash.tar.gz
cd ward-bash
./setup-ward.sh
```

## 🏁 빠른 시작

### 프로젝트 초기화
```bash
# 새 프로젝트 생성
ward-init my-project
cd my-project

# 기본 정책 확인
ward-cli status
```

### 첫 정책 생성
```bash
# .ward 파일 생성
echo "@description: My secure project
@whitelist: ls cat pwd echo grep sed awk git
@allow_comments: true
@max_comments: 5
@comment_prompt: \"Explain changes from a security perspective\"" > .ward

# 정책 검증
ward-cli check .
```

## 🔧 사용법

### 기본 명령어
```bash
# 시스템 상태 확인
ward-cli status

# 디렉토리 정책 분석
ward-cli check .

# 모든 정책 검증
ward-cli validate

# 보안 쉘 실행
ward-shell
```

### AI 협업
```bash
# AI 작업 핸들 추가
ward-cli handle add "Refactor authentication module" --comment "Improve security and add rate limiting"

# 핸들 목록 보기
ward-cli handle list

# 댓글 추가
ward-cli comment "This change improves performance by 20%" --context "backend optimization"
```

## 🐳 Docker 사용

### 기본 Docker 명령어
```bash
# 현재 디렉토리에서 Ward 실행
docker run -it --rm -v $(pwd):/workspace yamonco/ward:latest

# 커스텀 정책으로 실행
docker run -it --rm -v $(pwd):/workspace \
  -e WARD_POLICY_WHITELIST="ls cat pwd echo git" \
  yamonco/ward:latest
```

### Docker Compose 예제
```yaml
# docker-compose.yml
version: '3.8'
services:
  ward:
    image: yamonco/ward:latest
    volumes:
      - .:/workspace
    working_dir: /workspace
    environment:
      - WARD_LOG_LEVEL=INFO
      - WARD_POLICY_ALLOW_COMMENTS=true
    command: ward-shell
```

## 📋 정책 예제

### 프론트엔드 개발
```bash
echo "@description: Frontend application
@whitelist: ls cat pwd echo grep sed awk npm yarn node git code vim nano
@blacklist: rm mv cp chmod chown sudo
@allow_comments: true
@max_comments: 10
@comment_prompt: \"Explain changes from a frontend architecture perspective\"" > .ward
```

### 백엔드 개발
```bash
echo "@description: Backend API server
@whitelist: ls cat pwd echo grep sed awk python pip poetry docker git
@blacklist: rm -rf / rm mv cp sudo su
@allow_comments: true
@max_comments: 8
@comment_prompt: \"Explain changes from a backend security perspective\"" > .ward
```

### 시스템 관리
```bash
echo "@description: System administration tasks
@whitelist: ls cat pwd echo grep sed awk systemctl journalctl docker kubectl git vim nano
@blacklist: rm -rf /* dd format fdisk
@allow_comments: true
@max_comments: 3
@comment_prompt: \"Explain changes from a system administration perspective\"" > .ward
```

## 🔒 보안 모범 사례

### 프로덕션 환경 설정
```bash
# 인증 활성화
ward-cli auth set-password

# 감사 로깅 활성화
ward-cli config set engine.audit_enabled true
ward-cli config set logging.file_enabled true

# 엄격 모드 설정
ward-cli config set engine.strict_mode true
```

### 환경 변수 설정
```bash
export WARD_LOG_LEVEL=DEBUG
export WARD_STRICT_MODE=true
export WARD_PLUGIN_DIR=/custom/plugins
export WARD_AUTH_SESSION_TIMEOUT=7200
```

## 🛠️ 개발

### 로컬 개발 환경 설정
```bash
git clone https://github.com/yamonco/ward.git
cd ward
uv sync
source .venv/bin/activate

# 개발 모드로 설치
pip install -e .
```

### 테스트 실행
```bash
pytest tests/
```

## 📚 문서

- [상세 문서](.ward/README.md)
- [플러그인 개발 가이드](.ward/README.md#-plugins)
- [API 참조](.ward/README.md#-api-reference)

## 🤝 기여

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참조해주세요.

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. [LICENSE](LICENSE) 파일을 참조해주세요.

## 🆘 지원

- [GitHub Discussions](https://github.com/yamonco/ward/discussions)
- [이슈 보고](https://github.com/yamonco/ward/issues)
- [보안 취약점 보고](security@yamonco.com)

## 🏢 yamonco

Ward는 [yamonco](https://github.com/yamonco)에서 개발하고 유지보수하는 오픈소스 프로젝트입니다.

## ❤️ 스폰서

이 프로젝트가 도움이 되셨다면 GitHub Sponsors를 통해 지원해주세요:

[![Sponsor yamonco](https://img.shields.io/github/sponsors/yamonco?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sponsors/yamonco)

여러분의 지원은 다음과 같은 곳에 사용됩니다:
- 🐛 버그 수정 및 유지보수
- ✨ 새로운 기능 개발
- 📚 문서 개선
- 🔧 인프라 비용
- 🌍 커뮤니티 지원

---

**🚀 Ward Security System - Protecting your code, empowering your team**