# Contributing to Ward Security System

감사합니다! Ward 프로젝트에 기여해주셔서 감사합니다. 이 가이드는 프로젝트에 기여하는 방법을 설명합니다.

## 🤝 기여 방법

### 이슈 보고

버그를 발견하거나 기능 요청이 있으시면 [GitHub Issues](https://github.com/yamonco/ward/issues)를 통해 알려주세요.

#### 버그 리포트
- **제목**: 간결하고 명확한 버그 설명
- **환경**: 운영체제, 파이썬 버전, Ward 버전
- **재현 단계**: 버그를 재현할 수 있는 정확한 단계
- **기대 동작**: 어떻게 동작해야 하는지
- **실제 동작**: 실제로 어떻게 동작하는지
- **스크린샷**: 가능한 경우 스크린샷 첨부
- **로그**: 관련 로그 파일 첨부

#### 기능 요청
- **제목**: 요청하는 기능에 대한 간결한 설명
- **문제점**: 해결하려는 문제 설명
- **제안 해결책**: 원하는 솔루션 설명
- **대안**: 고려한 다른 해결책
- **추가 context**: 기타 관련 정보

### 코드 기여

#### 개발 환경 설정

1. 저장소 포크 및 클론
```bash
git clone https://github.com/YOUR_USERNAME/ward.git
cd ward
```

2. 개발 환경 설정
```bash
# UV 사용 (권장)
uv sync
source .venv/bin/activate

# 또는 pip 사용
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

3. pre-commit 훅 설정
```bash
pre-commit install
```

#### 브랜치 전략

- `main`: 안정적인 릴리스 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 새 기능 개발 브랜치
- `bugfix/*`: 버그 수정 브랜치
- `hotfix/*`: 긴급 수정 브랜치

#### 코드 스타일

프로젝트는 다음 도구들을 사용하여 코드 스타일을 유지합니다:

- **Black**: 코드 포맷팅
- **isort**: 임포트 정렬
- **flake8**: 린팅
- **mypy**: 타입 체킹

```bash
# 코드 스타일 검사
black src tests
isort src tests
flake8 src tests
mypy src
```

#### 테스트

모든 코드 변경은 테스트를 포함해야 합니다:

```bash
# 테스트 실행
pytest tests/

# 커버리지 확인
pytest tests/ --cov=src --cov-report=html

# 특정 테스트 실행
pytest tests/test_cli.py
```

#### Pull Request 프로세스

1. **브랜치 생성**
```bash
git checkout -b feature/your-feature-name
```

2. **코드 작성 및 테스트**
```bash
# 코드 작성
# 테스트 작성
# 모든 테스트 통과 확인
pytest tests/
```

3. **커밋**
```bash
git add .
git commit -m "feat: add new feature description"
```

4. **푸시 및 PR 생성**
```bash
git push origin feature/your-feature-name
```

5. **Pull Request 템플릿 작성**
   - 변경사항 요약
   - 테스트 방법
   - 관련 이슈 링크
   - 스크린샷 (해당하는 경우)

#### 커밋 메시지 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/) 규약을 따릅니다:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**타입:**
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 스타일 변경 (로직 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 프로세스, 보조 도구 변경

**예시:**
```
feat(cli): add verbose logging option

Added --verbose flag to enable detailed logging output
for debugging and troubleshooting.

Closes #123
```

## 🔧 개발 가이드

### 프로젝트 구조

```
ward/
├── src/ward_security/          # 파이썬 소스 코드
│   ├── __init__.py
│   ├── cli.py                  # CLI 인터페이스
│   ├── shell.py                # 보안 쉘
│   ├── installer.py            # 설치 관리자
│   └── deployer.py             # 배포 관리자
├── .ward/                      # Bash 스크립트 및 설정
│   ├── core/                   # 핵심 기능
│   ├── ward-cli.sh            # CLI 스크립트
│   └── ward.sh                # 메인 스크립트
├── tests/                      # 테스트 코드
├── docs/                       # 문서
└── .github/                    # GitHub 설정
```

### 코딩 표준

1. **타입 힌트**: 모든 함수에는 타입 힌트 사용
```python
def process_command(command: str, args: List[str]) -> int:
    """Process a command with arguments."""
    pass
```

2. **독스트링**: 모든 모듈, 클래스, 함수에 독스트링 작성
```python
class WardCLI:
    """Ward Security Command Line Interface.

    Provides a Python wrapper around the Ward CLI bash script
    for better integration with Python-based workflows.
    """
```

3. **에러 처리**: 구체적인 예외 처리
```python
try:
    result = subprocess.run(command, check=True)
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e}")
    raise WardError(f"Command execution failed: {e}") from e
```

4. **로깅**: 구조화된 로깅 사용
```python
import logging

logger = logging.getLogger(__name__)

def execute_command(command: str) -> int:
    logger.info(f"Executing command: {command}")
    try:
        result = run_command(command)
        logger.debug(f"Command result: {result}")
        return result
    except Exception as e:
        logger.error(f"Command failed: {e}")
        raise
```

### 테스트 가이드

#### 단위 테스트
```python
import pytest
from ward_security.cli import WardCLI

class TestWardCLI:
    def test_init_success(self):
        cli = WardCLI()
        assert cli.ward_root is not None

    def test_run_command_invalid_cli(self, tmp_path):
        cli = WardCLI()
        cli.ward_cli_path = tmp_path / "nonexistent.sh"
        result = cli.run_ward_command(["status"])
        assert result == 1
```

#### 통합 테스트
```python
def test_full_workflow(tmp_path):
    # 테스트용 .ward 파일 생성
    ward_file = tmp_path / ".ward"
    ward_file.write_text("@description: Test project\n@whitelist: ls cat pwd\n")

    # CLI 실행
    result = run_cli(["check", str(tmp_path)])
    assert result.returncode == 0
```

## 📝 문서 기여

### 문서 유형

- **API 문서**: 코드 독스트링에 포함
- **사용자 가이드**: `docs/` 디렉토리
- **개발자 가이드**: `CONTRIBUTING.md`
- **릴리스 노트**: GitHub Releases

### 문서 작성 가이드

1. **마크다운 형식** 사용
2. **코드 예제** 포함
3. **스크린샷** 첨부 (적절한 경우)
4. **링크 검증** (모든 링크가 유효한지 확인)

## 🚀 릴리스 프로세스

### 버전 관리

[Semantic Versioning](https://semver.org/)을 따릅니다:

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 호환되지 않는 API 변경
- `MINOR`: 새 기능 추가 (하위 호환)
- `PATCH`: 버그 수정 (하위 호환)

### 릴리스 체크리스트

- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 문서 업데이트
- [ ] CHANGELOG.md 업데이트
- [ ] 버전 번호 업데이트
- [ ] 태그 생성
- [ ] GitHub Release 생성
- [ ] Docker 이미지 빌드 및 푸시
- [ ] PyPI에 배포

## 🏅 기여자 인정

모든 기여자는 다음과 같이 인정받습니다:

- **README.md**: 기여자 목록
- **릴리스 노트**: 특정 릴리스에 기여한 사람들
- **GitHub Contributors**: 자동으로 기여자 추적

## 📞 도움말

기여 과정에서 도움이 필요하시면:

- **GitHub Discussions**: 질문 및 토론
- **Issues**: 버그 리포트 및 기능 요청
- **Email**: dev@yamonco.com

## 📄 라이선스

기여하는 모든 코드는 프로젝트의 [MIT 라이선스](LICENSE) 하에 배포됩니다. 기여함으로써 라이선스 조건에 동의하는 것으로 간주합니다.

---

다시 한번 기여해주셔서 감사합니다! 🙏