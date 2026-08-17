#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TMP_HOME"' EXIT

MINIMAL_PATH="/usr/bin:/bin:/usr/sbin:/sbin"

run_installer() {
  env -i HOME="$TMP_HOME" PATH="$MINIMAL_PATH" bash "$ROOT/install.sh" "$@" --dry-run
}

assert_contains() {
  local output="$1" expected="$2"
  if [[ "$output" != *"$expected"* ]]; then
    printf 'expected output to contain: %s\n' "$expected" >&2
    printf 'actual output:\n%s\n' "$output" >&2
    exit 1
  fi
}

assert_not_contains() {
  local output="$1" unexpected="$2"
  if [[ "$output" == *"$unexpected"* ]]; then
    printf 'expected output not to contain: %s\n' "$unexpected" >&2
    printf 'actual output:\n%s\n' "$output" >&2
    exit 1
  fi
}

codex_without_target_output="$(run_installer --codex-only)"
assert_contains "$codex_without_target_output" "== Codex: 건너뜀"
assert_not_contains "$codex_without_target_output" "+ ln -s $ROOT/codex/skills/humanize-korean"

mkdir -p "$TMP_HOME/.codex"
codex_output="$(run_installer --codex-only)"
assert_contains "$codex_output" "== Codex =="
assert_contains "$codex_output" "+ ln -s $ROOT/codex/skills/humanize-korean $TMP_HOME/.codex/skills/humanize-korean"
assert_not_contains "$codex_output" "Codex: "
rm -rf "$TMP_HOME/.codex"

claude_without_target_output="$(run_installer --claude-only)"
assert_contains "$claude_without_target_output" "== Claude Code: 건너뜀"
assert_not_contains "$claude_without_target_output" "+ ln -s $ROOT/.claude/skills/humanize-korean"

mkdir -p "$TMP_HOME/.claude"
claude_output="$(run_installer --claude-only)"
assert_contains "$claude_output" "== Claude Code =="
assert_contains "$claude_output" "+ ln -s $ROOT/.claude/skills/humanize-korean $TMP_HOME/.claude/skills/humanize-korean"
assert_not_contains "$claude_output" "Claude Code: "
rm -rf "$TMP_HOME/.claude"

mkdir -p "$TMP_HOME/.codex"
codex_desktop_output="$(run_installer)"
assert_contains "$codex_desktop_output" "== Codex =="
assert_contains "$codex_desktop_output" "+ ln -s $ROOT/codex/skills/humanize-korean $TMP_HOME/.codex/skills/humanize-korean"
assert_not_contains "$codex_desktop_output" "Codex: "
rm -rf "$TMP_HOME/.codex"

mkdir -p "$TMP_HOME/.claude"
claude_desktop_output="$(run_installer)"
assert_contains "$claude_desktop_output" "== Claude Code =="
assert_contains "$claude_desktop_output" "+ ln -s $ROOT/.claude/skills/humanize-korean $TMP_HOME/.claude/skills/humanize-korean"
assert_not_contains "$claude_desktop_output" "Claude Code: "
rm -rf "$TMP_HOME/.claude"

# 에이전트 선별 설치 — 기본은 스킬이 실제로 쓰는 4종만.
# agents/ 의 나머지 5종은 릴리스 회차용 개발 도구라 전역 풀에 상주시키지 않는다.
RUNTIME_AGENTS="humanize-monolith humanize-diagnostician humanize-finalizer korean-ai-tell-taxonomist"
DEV_ONLY_AGENTS="translationese-research-distiller korean-translation-scholar taxonomy-gap-analyzer post-editese-metric-engineer quick-rules-integrator"

mkdir -p "$TMP_HOME/.claude"
default_agents_output="$(run_installer --claude-only)"
for a in $RUNTIME_AGENTS; do
  assert_contains "$default_agents_output" "+ ln -s $ROOT/agents/$a.md $TMP_HOME/.claude/agents/$a.md"
done
for a in $DEV_ONLY_AGENTS; do
  assert_not_contains "$default_agents_output" "$ROOT/agents/$a.md"
done

all_agents_output="$(run_installer --claude-only --all-agents)"
for a in "$ROOT"/agents/*.md; do
  assert_contains "$all_agents_output" "+ ln -s $a $TMP_HOME/.claude/agents/$(basename "$a")"
done
rm -rf "$TMP_HOME/.claude"

echo "install flag tests passed"
