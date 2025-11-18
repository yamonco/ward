#!/usr/bin/env bash
# .ward/ward-completion.bash - 와드 명령어 자동 완성

_ward_completion() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="status check validate debug test help"

    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi

    case "${prev}" in
        "check"|"debug")
            # 디렉터리 경로 자동 완성
            COMPREPLY=( $(compgen -d -- ${cur}) )
            return 0
            ;;
        "test")
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                # 명령어 자동 완성
                COMPREPLY=( $(compgen -W "mkdir rm mv cp touch cat ls" -- ${cur}) )
            elif [[ ${COMP_CWORD} -eq 3 ]]; then
                # 경로 자동 완성
                COMPREPLY=( $(compgen -f -- ${cur}) )
            fi
            return 0
            ;;
    esac
}

complete -F _ward_completion ward
complete -F _ward_completion ./ward
complete -F _ward_completion .ward/ward.sh