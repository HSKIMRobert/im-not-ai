#!/usr/bin/env bash
# Humanize KR — Claude Code + Codex CLI + Gemini CLI 전역 설치 스크립트
# 저장소를 클론한 뒤 `./install.sh` 한 번이면 설치된 CLI(claude/codex/gemini)를 자동 감지해
# humanize-korean 스킬(+ 에이전트)을 전역으로 연결한다. 기본은 심링크(저장소 수정 즉시 반영).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

MODE=symlink          # symlink | copy
DO_CLAUDE=auto        # auto | yes | no
DO_CODEX=auto
DO_GEMINI=auto
FORCE=0
DRYRUN=0
ALL_AGENTS=0
TS="$(date +%Y%m%d-%H%M%S)"

# 스킬 런타임이 호출하는 3종 + 별도 명령으로만 트리거되는 유지보수 1종.
# agents/ 의 나머지(릴리스 회차용 개발 도구)는 --all-agents 일 때만 설치한다 —
# 서브에이전트는 description 매칭으로 자동 라우팅되므로, 윤문과 무관한 정의가
# 전역 풀에 상주하면 다른 작업에서 잘못 호출될 수 있다.
INSTALLED_AGENTS="humanize-monolith humanize-diagnostician humanize-finalizer korean-ai-tell-taxonomist"

print_help() {
  cat <<'H'
Usage: ./install.sh [options]

  설치된 CLI를 자동 감지해 humanize-korean 스킬을 전역 설치한다.
  Claude: ~/.claude/skills/{humanize-korean,humanize,humanize-redo} + ~/.claude/agents/*.md
  Codex : ~/.codex/skills/humanize-korean
  Gemini: gemini extensions link (gemini-extension.json + GEMINI.md + commands/)

Options:
  --copy          심링크 대신 복사(저장소를 지워도 유지, references 심링크는 실체화).
                  ※ 복사본은 uninstall.sh가 자동 삭제하지 않음(수동 삭제).
  --claude-only   Claude만 설치 시도(claude 명령 또는 ~/.claude 감지 시)
  --codex-only    Codex만 설치 시도(codex 명령 또는 ~/.codex 감지 시)
  --gemini-only   Gemini만 설치
  --no-gemini     Gemini 건너뜀 (claude/codex만)
  --all-agents    agents/ 전체를 전역 설치(개발용 1회성 정의 포함).
                  기본은 스킬이 실제로 쓰는 4종만 — 런타임 3(monolith·
                  diagnostician·finalizer) + 유지보수 1(taxonomist).
  --force         대상에 일반 파일/디렉토리가 있어도 .bak.<ts> 백업 후 덮어씀
  --dry-run       실제 변경 없이 수행할 작업만 출력
  -h, --help      이 도움말

Env overrides: CLAUDE_HOME(기본 ~/.claude), CODEX_HOME(기본 ~/.codex)
H
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --claude-only) DO_CODEX=no; DO_GEMINI=no ;;
    --codex-only) DO_CLAUDE=no; DO_GEMINI=no ;;
    --gemini-only) DO_CLAUDE=no; DO_CODEX=no; DO_GEMINI=yes ;;
    --no-gemini) DO_GEMINI=no ;;
    --all-agents) ALL_AGENTS=1 ;;
    --force) FORCE=1 ;;
    --dry-run) DRYRUN=1 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "unknown arg: $1" >&2; print_help; exit 2 ;;
  esac
  shift
done

run() { echo "+ $*"; [ "$DRYRUN" = 1 ] || "$@"; }

# rc: 0=대상 비었음(설치 진행) / 1=이미 우리 심링크(스킵) / 2=충돌(거부)
prepare_target() {
  local dest="$1" src="$2"
  if [ -L "$dest" ]; then
    if [ "$(readlink "$dest")" = "$src" ]; then
      echo "ok (already linked): $dest"; return 1
    fi
    run mv "$dest" "$dest.bak.$TS"
  elif [ -e "$dest" ]; then
    if [ "$FORCE" != 1 ]; then
      echo "refuse: $dest 가 이미 있음 (--force 로 백업 후 덮어쓰기 또는 --copy)"; return 2
    fi
    run mv "$dest" "$dest.bak.$TS"
  fi
  return 0
}

install_one() {
  local src="$1" dest="$2"
  run mkdir -p "$(dirname "$dest")"
  local rc=0
  prepare_target "$dest" "$src" || rc=$?
  [ "$rc" = 1 ] && return 0
  [ "$rc" = 2 ] && return 1
  case "$MODE" in
    symlink) run ln -s "$src" "$dest" ;;
    copy)    run cp -RL "$src" "$dest" ;;   # -L: references 심링크를 실체로 복사
  esac
  echo "installed: $dest"
}

# CLI 명령 또는 홈 디렉터리(앱만 설치한 사용자)로 대상 감지
has_claude_target() { command -v claude >/dev/null 2>&1 || [ -d "$CLAUDE_HOME" ]; }
has_codex_target()  { command -v codex  >/dev/null 2>&1 || [ -d "$CODEX_HOME" ]; }

# ---- Claude ----
if [ "$DO_CLAUDE" != no ] && { [ "$DO_CLAUDE" = yes ] || has_claude_target; }; then
  echo "== Claude Code =="
  run mkdir -p "$CLAUDE_HOME/skills" "$CLAUDE_HOME/agents"
  for s in humanize-korean humanize humanize-redo; do
    install_one "$REPO/.claude/skills/$s" "$CLAUDE_HOME/skills/$s"
  done
  agents=()
  if [ "$ALL_AGENTS" = 1 ]; then
    for a in "$REPO/agents"/*.md; do
      if [ -e "$a" ]; then agents[${#agents[@]}]="$a"; fi
    done
  else
    for n in $INSTALLED_AGENTS; do
      if [ -f "$REPO/agents/$n.md" ]; then
        agents[${#agents[@]}]="$REPO/agents/$n.md"
      else
        echo "warn: agents/$n.md 를 찾지 못해 건너뜀" >&2
      fi
    done
  fi
  if [ "${#agents[@]}" -gt 0 ]; then
    for a in "${agents[@]}"; do
      install_one "$a" "$CLAUDE_HOME/agents/$(basename "$a")"
    done
  fi
  if [ "$ALL_AGENTS" != 1 ]; then
    echo "note: 릴리스 회차용 개발 에이전트는 설치하지 않음 (전체 설치는 --all-agents)"
  fi
else
  echo "== Claude Code: 건너뜀 (claude 또는 $CLAUDE_HOME 미감지) =="
fi

# ---- Codex ----
if [ "$DO_CODEX" != no ] && { [ "$DO_CODEX" = yes ] || has_codex_target; }; then
  echo "== Codex =="
  run mkdir -p "$CODEX_HOME/skills"
  install_one "$REPO/codex/skills/humanize-korean" "$CODEX_HOME/skills/humanize-korean"
else
  echo "== Codex: 건너뜀 (codex 또는 $CODEX_HOME 미감지) =="
fi

# ---- Gemini CLI ----
if [ "$DO_GEMINI" != no ] && { [ "$DO_GEMINI" = yes ] || command -v gemini >/dev/null 2>&1; }; then
  echo "== Gemini CLI =="
  if [ "$DRYRUN" = 1 ]; then
    echo "+ gemini extensions link $REPO (dry-run)"
  else
    echo "gemini extensions link \"$REPO\" 실행 (확장 등록)..."
    echo "Y" | gemini extensions link "$REPO" 2>/dev/null && echo "installed: Gemini extension (im-not-ai)" \
      || echo "  (이미 등록됨 또는 수동 등록 필요: gemini extensions link $REPO)"
  fi
else
  echo "== Gemini CLI: 건너뜀 (gemini 미감지 — 강제하려면 --gemini-only) =="
fi

echo ""
echo "완료 (mode=$MODE)."
echo "  Claude: 새 세션에서 /humanize-korean (또는 /humanize)"
echo "  Codex : \$humanize-korean"
echo "  Gemini: 새 세션에서 /humanize-korean (또는 /humanize)"
echo "  업데이트: ./update.sh (새 버전 자동 감지 + 적용) · 제거: ./uninstall.sh"
exit 0
