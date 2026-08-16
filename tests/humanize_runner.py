"""Live humanize runner — 배포된 humanize-korean 스킬을 `claude -p`로 실제 호출.

살아있는 스킬을 돌려 갓 나온 윤문본을 얻는다. test_humanize_live.py와
generate_fixtures.py가 공유한다. `claude` CLI(Claude Code, 구독 인증)만 있으면 되고
별도 API 키는 필요 없다. 스킬은 이 레포의 .claude/skills/humanize-korean 에서 탐색됨
(claude 를 레포 루트에서 실행).
"""
from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_START, _END = "<<<H>>>", "<<</H>>>"
_SENTINEL = re.compile(re.escape(_START) + r"(.*?)" + re.escape(_END), re.S)

CLAUDE_BIN = shutil.which("claude")


class SkillUnavailable(RuntimeError):
    """claude CLI 부재 / 타임아웃 / 출력 파싱 실패."""


def _prompt(
    text: str,
    strict: bool,
    protected_tokens: Sequence[str] = (),
    max_change_rate: float = 0.50,
    retry_reason: str = "",
) -> str:
    mode = "strict(5인 파이프라인)" if strict else "Fast"
    protected = ""
    if protected_tokens:
        encoded = json.dumps(list(protected_tokens), ensure_ascii=False)
        protected = (
            f"하드 불변식: 다음 보호 토큰은 결과에 정확히 그대로 남겨: {encoded}. "
        )
    retry = f"직전 시도는 {retry_reason}. 원문 문장을 더 많이 유지해 다시 써. " if retry_reason else ""
    return (
        f"다음 텍스트를 humanize-korean 스킬 {mode} 모드로 윤문해줘. "
        "원문 주장의 핵심 내용 명사·개념어는 조사·어미 외 원형을 그대로 보존하고, "
        f"이미 자연스러운 구간은 손대지 말며, 문자 단위 변경률은 {max_change_rate * 100:g}% 이하로 유지해. "
        f"{protected}"
        f"{retry}"
        f"설명·헤딩·지표 전부 빼고, 윤문된 본문만 반드시 {_START} 와 {_END} 사이에 "
        f"한 덩어리로 출력해. 파일은 만들지 마.\n\n텍스트:\n" + text
    )


def run_humanize(
    text: str,
    *,
    strict: bool = False,
    protected_tokens: Sequence[str] = (),
    max_change_rate: float = 0.50,
    timeout: int = 300,
) -> str:
    """스킬을 실제 호출하고 하드 불변식 위반 시 한 번 보수 재실행한다."""
    if not CLAUDE_BIN:
        raise SkillUnavailable("`claude` CLI를 찾을 수 없음 (Claude Code 설치 필요)")
    result = ""
    retry_reason = ""
    for attempt in range(2):
        try:
            proc = subprocess.run(
                [
                    CLAUDE_BIN,
                    "-p",
                    _prompt(
                        text,
                        strict,
                        protected_tokens,
                        max_change_rate,
                        retry_reason,
                    ),
                ],
                cwd=_REPO_ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SkillUnavailable(f"claude 호출 타임아웃 ({timeout}s)") from exc

        out = proc.stdout or ""
        match = _SENTINEL.search(out)
        if not match:
            raise SkillUnavailable(f"센티넬 파싱 실패. 원출력 앞부분: {out[:200]!r}")
        result = match.group(1).strip()

        missing = [token for token in protected_tokens if token not in result]
        rate = 1.0 - difflib.SequenceMatcher(None, text, result).ratio()
        violations = []
        if missing:
            violations.append(f"보호 토큰 유실({', '.join(missing)})")
        if rate > max_change_rate:
            violations.append(
                f"변경률 {rate * 100:.1f}%가 상한 {max_change_rate * 100:g}% 초과"
            )
        if not violations or attempt == 1:
            return result
        retry_reason = ", ".join(violations)
        print(
            f"[humanize-live] retry 1/1 after gate violation: {retry_reason}",
            file=sys.stderr,
            flush=True,
        )

    return result
