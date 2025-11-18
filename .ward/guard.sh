#!/usr/bin/env bash
# .ward/guard.sh
# - ward-shell 에서만 BASH_ENV 로 로딩된다.
# - .ward 프리텍스트 포맷 + 상위 와드 병합 지원
# - v1: mkdir만 가드 (mv/cp/rm은 동일 패턴으로 확장 가능)

shopt -s expand_aliases 2>/dev/null || true

########################################
# 기본 환경
########################################

# WARD_ROOT: 레포 루트 (ward-shell에서 export)
if [[ -z "$WARD_ROOT" ]]; then
  WARD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

########################################
# 경로 유틸
########################################

# 경로를 절대경로로 정규화
_ward_resolve() {
  local raw="$1"
  realpath -m -- "$raw" 2>/dev/null || printf '%s\n' "$raw"
}

# 주어진 "절대경로" 기준으로, WARD_ROOT 까지만 올라가며
# 발견한 모든 .ward 파일을 child->parent 순서로 배열에 담는다.
_ward_collect_files() {
  local path="$1"
  local dir
  WARD_COLLECTED=()

  if [[ -d "$path" ]]; then
    dir="$path"
  else
    dir="$(dirname "$path")"
  fi

  while :; do
    # 루트 범위 밖으로 나가면 중단
    case "$dir" in
      "$WARD_ROOT"/*|"$WARD_ROOT")
        ;;
      *)
        # WARD_ROOT 위까지 갔으면 종료
        [[ "$dir" == "/" ]] && break
        dir="$(dirname "$dir")"
        continue
        ;;
    esac

    if [[ -f "$dir/.ward" ]]; then
      WARD_COLLECTED+=("$dir/.ward")
    fi

    [[ "$dir" == "$WARD_ROOT" ]] && break
    dir="$(dirname "$dir")"
  done
}

########################################
# .ward 프리텍스트 파서 + 병합
########################################

# 전역 누적 변수
WARD_DESCRIPTION=""
WARD_PROMPT=""
WARD_WHITELIST=""       # "ls cat" 이런 식으로 공백 구분
WARD_BLACKLIST=""       # 동일
WARD_LOCK_NEW_DIRS=""   # "true"/"false"/""(unset)
WARD_LOCK_WRITES=""     # "true"/"false"/""(unset)
WARD_ALLOW_COMMENTS=""  # "true"/"false"/""(unset)
WARD_MAX_COMMENTS=""    # 숫자 또는 ""(unset)
WARD_COMMENT_PROMPT=""  # 댓글용 프롬프트
WARD_EXPLAIN_ON_ERROR=""   # "true"/"false"/""(unset)

# 한 줄 앞/뒤 공백 제거
_ward_trim() {
  local s="$1"
  # 앞 공백 제거
  s="${s#"${s%%[![:space:]]*}"}"
  # 뒤 공백 제거
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

# 하나의 .ward 파일을 읽어 전역 누적 변수에 "병합" 적용
# - 상위에서 먼저 호출, 하위에서 나중에 호출하면 override가 자연스럽게 된다.
_ward_apply_file() {
  local file="$1"
  local line key val

  while IFS='' read -r line || [[ -n "$line" ]]; do
    # 빈 라인 처리
    [[ -z "$line" ]] && continue

    case "$line" in
      @description:*)
        val="${line#@description:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          if [[ -n "$WARD_DESCRIPTION" ]]; then
            WARD_DESCRIPTION+=$'\n'"$val"
          else
            WARD_DESCRIPTION="$val"
          fi
        fi
        ;;
      @prompt:*)
        val="${line#@prompt:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          if [[ -n "$WARD_PROMPT" ]]; then
            WARD_PROMPT+=$'\n'"$val"
          else
            WARD_PROMPT="$val"
          fi
        fi
        ;;
      @whitelist:*)
        val="${line#@whitelist:}"
        val=$(_ward_trim "$val")
        # 비어있지 않다면 상위 값 override
        if [[ -n "$val" ]]; then
          WARD_WHITELIST="$val"
        fi
        ;;
      @blacklist:*)
        val="${line#@blacklist:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          WARD_BLACKLIST="$val"
        fi
        ;;
      @lock_new_dirs:*)
        val="${line#@lock_new_dirs:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          WARD_LOCK_NEW_DIRS="$val"
        fi
        ;;
      @lock_writes:*)
        val="${line#@lock_writes:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          WARD_LOCK_WRITES="$val"
        fi
        ;;
      @allow_comments:*)
        val="${line#@allow_comments:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          WARD_ALLOW_COMMENTS="$val"
        fi
        ;;
      @max_comments:*)
        val="${line#@max_comments:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          WARD_MAX_COMMENTS="$val"
        fi
        ;;
      @comment_prompt:*)
        val="${line#@comment_prompt:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          if [[ -n "$WARD_COMMENT_PROMPT" ]]; then
            WARD_COMMENT_PROMPT+=$'\n'"$val"
          else
            WARD_COMMENT_PROMPT="$val"
          fi
        fi
        ;;
      @explain_on_error:*)
        val="${line#@explain_on_error:}"
        val=$(_ward_trim "$val")
        if [[ -n "$val" ]]; then
          WARD_EXPLAIN_ON_ERROR="$val"
        fi
        ;;
      @*)
        # 알 수 없는 @지시자는 그냥 무시
        ;;
      *)
        # 나머지는 전부 description 텍스트로 간주
        if [[ -n "$line" ]]; then
          if [[ -n "$WARD_DESCRIPTION" ]]; then
            WARD_DESCRIPTION+=$'\n'"$line"
          else
            WARD_DESCRIPTION="$line"
          fi
        fi
        ;;
    esac
  done < "$file"
}

# 최종 정책 기반 거부 메시지
_ward_deny() {
  local cmd="$1" path="$2"

  # boolean 디폴트 처리
  local explain="${WARD_EXPLAIN_ON_ERROR}"
  [[ -z "$explain" ]] && explain="true"

  printf '%s: cannot operate on %s: Permission denied\n' "$cmd" "$path" >&2

  [[ "$explain" != "true" ]] && return 0

  printf '[WARD] 이 위치는 와드에 의해 잠겨 있습니다.\n' >&2

  if [[ -n "$WARD_DESCRIPTION" ]]; then
    printf '해설:\n%s\n' "$WARD_DESCRIPTION" >&2
  fi

  # 정책 요약 텍스트
  printf '정책: whitelist=[%s], blacklist=[%s], lock_new_dirs=%s, lock_writes=%s, explain_on_error=%s\n' \
    "$WARD_WHITELIST" "$WARD_BLACKLIST" \
    "${WARD_LOCK_NEW_DIRS:-unset}" "${WARD_LOCK_WRITES:-unset}" "${WARD_EXPLAIN_ON_ERROR:-unset}" >&2

  if [[ -n "$WARD_PROMPT" ]]; then
    printf '프롬프트:\n%s\n' "$WARD_PROMPT" >&2
  fi
}

# 경로 하나에 대한 최종 정책을 계산하고, cmd 기준으로 허용/거부 결정
# 허용: 0, 거부: 1, 와드 없음: 0
_ward_eval_policy_for_path() {
  local cmd="$1" path="$2"

  # 상위 .ward 파일들 수집 (child->parent)
  _ward_collect_files "$path"

  local count="${#WARD_COLLECTED[@]}"

  # 와드 파일이 하나도 없으면 통과
  if (( count == 0 )); then
    return 0
  fi

  # 누적 변수 초기화
  WARD_DESCRIPTION=""
  WARD_PROMPT=""
  WARD_WHITELIST=""
  WARD_BLACKLIST=""
  WARD_LOCK_NEW_DIRS=""
  WARD_LOCK_WRITES=""
  WARD_ALLOW_COMMENTS=""
  WARD_MAX_COMMENTS=""
  WARD_COMMENT_PROMPT=""
  WARD_EXPLAIN_ON_ERROR=""

  # parent → child 순서로 적용해야 하므로 배열 역순으로 돌린다.
  local i
  for (( i = count - 1; i >= 0; i-- )); do
    _ward_apply_file "${WARD_COLLECTED[$i]}"
  done

  # ------------------------------------------------------------------
  # 여기서부터 최종 값(WARD_*) 기준으로 cmd 허용/거부 판단
  # ------------------------------------------------------------------

  local wl="$WARD_WHITELIST"
  local bl="$WARD_BLACKLIST"
  local lock_new="${WARD_LOCK_NEW_DIRS}"

  # 1) whitelist: 값이 있으면, 여기에 없는 cmd 는 전부 금지
  if [[ -n "$wl" ]]; then
    if ! grep -qw -- "$cmd" <<<"$wl"; then
      _ward_deny "$cmd" "$path"
      return 1
    fi
  fi

  # 2) blacklist: 값이 있고, 거기에 cmd 가 있으면 금지
  if [[ -n "$bl" ]]; then
    if grep -qw -- "$cmd" <<<"$bl"; then
      _ward_deny "$cmd" "$path"
      return 1
    fi
  fi

  # 3) lock_new_dirs: mkdir + 아직 없는 경로면 금지
  if [[ "$cmd" == "mkdir" && "$lock_new" == "true" ]]; then
    if [[ ! -e "$path" ]]; then
      _ward_deny "$cmd" "$path"
      return 1
    fi
  fi

  # (lock_writes 는 나중에 open/append 래핑 구현할 때 사용)

  return 0
}

########################################
# 댓글 관련 유틸리티
########################################

# 와드 파일의 댓글 개수 세기
_ward_count_comments() {
  local ward_file="$1"
  if [[ ! -f "$ward_file" ]]; then
    echo 0
    return
  fi

  # #로 시작하는 라인 카운트 (단, @지시자 제외)
  grep "^#" "$ward_file" | grep -v "^# @" | wc -l
}

# 댓글 추가 가능 여부 확인
_ward_can_comment() {
  local path="$1"

  # 상위 .ward 파일들 수집
  _ward_collect_files "$path"
  local count="${#WARD_COLLECTED[@]}"

  if (( count == 0 )); then
    return 1  # 와드 파일이 없으면 댓글 불가
  fi

  # 정책 평가
  _ward_eval_policy_for_path "comment" "$path"
  return $?
}

# 댓글 최대 개수 확인
_ward_check_comment_limit() {
  local path="$1"
  local ward_file ward_dir

  if [[ -d "$path" ]]; then
    ward_dir="$path"
  else
    ward_dir="$(dirname "$path")"
  fi

  # 가장 가까운 와드 파일 찾기
  while [[ "$ward_dir" != "$WARD_ROOT" ]] && [[ "$ward_dir" != "/" ]]; do
    if [[ -f "$ward_dir/.ward" ]]; then
      ward_file="$ward_dir/.ward"
      break
    fi
    ward_dir="$(dirname "$ward_dir")"
  done

  if [[ -z "$ward_file" ]]; then
    return 0  # 와드 파일이 없으면 제한 없음
  fi

  # max_comments 설정 확인
  local max_comments
  max_comments=$(grep "^@max_comments:" "$ward_file" 2>/dev/null | sed 's/^@max_comments: //')

  if [[ -z "$max_comments" ]]; then
    return 0  # 제한 없음
  fi

  # 현재 댓글 개수 확인
  local current_comments
  current_comments=$(_ward_count_comments "$ward_file")

  if (( current_comments >= max_comments )); then
    return 1  # 제한 도달
  fi

  return 0  # 댓글 추가 가능
}

# 와드 파일에 댓글 추가
_ward_add_comment() {
  local ward_file="$1"
  local comment="$2"

  if [[ ! -f "$ward_file" ]]; then
    echo "Ward file not found: $ward_file" >&2
    return 1
  fi

  # 댓글 추가
  echo "# $comment" >> "$ward_file"
  return 0
}

########################################
# 명령 래핑 (v1: mkdir만)
########################################

_mkdir_impl() { command mkdir "$@"; }

mkdir() {
  local args=("$@")
  local arg resolved

  for arg in "${args[@]}"; do
    [[ "$arg" == -* ]] && continue  # -p 같은 옵션은 스킵

    resolved=$(_ward_resolve "$arg")

    # 이 경로에 대해 정책 평가
    if _ward_eval_policy_for_path "mkdir" "$resolved"; then
      # 허용 → 실제 mkdir 실행
      _mkdir_impl "$@"
      return $?
    else
      # 거부 → 이미 _ward_deny 가 메시지 출력
      return 1
    fi
  done

  # 경로 인자가 전혀 없거나, 와드가 전혀 없는 경우 → 그냥 실행
  _mkdir_impl "$@"
}

# handle 명령어 래퍼
handle() {
  local cmd="$1"
  local target="$2"
  local resolved

  if [[ -z "$cmd" ]]; then
    echo "Usage: handle <command> [target]" >&2
    return 1
  fi

  if [[ -n "$target" ]]; then
    resolved=$(_ward_resolve "$target")
  else
    resolved="$(pwd)"
  fi

  # 정책 평가
  if _ward_eval_policy_for_path "handle" "$resolved"; then
    # handle 명령어 실행 - 기본적으로는 아무것도 안 함
    echo "Handled: $cmd on $resolved"

    # 댓글 기능이 활성화되어 있고, @comment_prompt가 있으면 표시
    if [[ -n "$WARD_COMMENT_PROMPT" ]]; then
      echo
      echo "[WARD AI Comment Prompt]:"
      echo "$WARD_COMMENT_PROMPT"
      echo
      echo "Use 'comment <your comment>' to add AI-generated comment to .ward file"
    fi

    return 0
  else
    # 거부 → 이미 _ward_deny 가 메시지 출력
    return 1
  fi
}

# comment 명령어 래퍼
comment() {
  local comment_text="$*"
  local current_dir="$(pwd)"
  local ward_file ward_dir

  if [[ -z "$comment_text" ]]; then
    echo "Usage: comment <comment text>" >&2
    return 1
  fi

  # 현재 디렉터리의 와드 파일 찾기
  ward_dir="$current_dir"
  while [[ "$ward_dir" != "$WARD_ROOT" ]] && [[ "$ward_dir" != "/" ]]; do
    if [[ -f "$ward_dir/.ward" ]]; then
      ward_file="$ward_dir/.ward"
      break
    fi
    ward_dir="$(dirname "$ward_dir")"
  done

  if [[ -z "$ward_file" ]]; then
    echo "No .ward file found for current directory" >&2
    return 1
  fi

  # 댓글 권한 확인
  if ! _ward_can_comment "$current_dir"; then
    echo "Comments not allowed in this directory" >&2
    return 1
  fi

  # 댓글 제한 확인
  if ! _ward_check_comment_limit "$current_dir"; then
    echo "Maximum comment limit reached for this .ward file" >&2
    return 1
  fi

  # 댓글 추가
  if _ward_add_comment "$ward_file" "$comment_text"; then
    echo "Comment added to $(basename "$(dirname "$ward_file")")/.ward"
    echo "Comment: $comment_text"
    return 0
  else
    echo "Failed to add comment" >&2
    return 1
  fi
}