#!/usr/bin/env python3
"""서법 국소 복원 — 유보·요구가 사라진 문장만 원문 문장으로 되돌린다.

## 왜 필요한가

`verify_gates.py` P5는 당위·완곡 표지 총수가 줄면 **경고만** 한다. 판정은 하되 고치지는
않으므로, 실행자가 "단언으로 바꾸는" 편집을 하면 그 결과가 그대로 사용자에게 나간다.
규칙(A-10·G-1)을 보존 쪽으로 고쳐도 프롬프트는 확률적이라 계속 샌다 — 스킬을 실제로
돌린 A/B에서 v2.3·v2.4 양쪽 모두 "낮은 것으로 판단된다" → "낮은 수치다" 변환이 남았다.

이 스크립트는 그 변환만 **문장 단위로** 되돌린다. 패스 전체를 버리는 것보다 손실이 작다:
서법은 지키면서 나머지 윤문(번역투·상투구·대구 제거)은 살아남는다.

## 트레이드오프

되돌린 문장의 AI 티(예: "지금이야말로")도 함께 돌아온다. **의미 보존이 티 제거보다
우선한다**는 정책에 따른 선택이다.

## 안전 원칙 — 확실할 때만 손댄다

이 스크립트는 판정기가 아니라 **결과물을 바꾸는 변형기**다. 잘못 치환하면 게이트가
아니라 새 오류의 원인이 된다. 그래서 애매하면 건드리지 않고 보고만 한다(skipped):

- 짝 문장 유사도가 낮으면 정렬 아티팩트로 보고 건너뛴다
- 치환 대상이 결과 안에 정확히 한 번 나타날 때만 바꾼다(0=못 찾음, 2+=엉뚱한 쪽 치환 위험)
- 원문 문장에 없던 내용어가 여럿이면 두 문장이 합쳐진 것으로 보고 건너뛴다
  (되돌리면 합쳐진 다른 명제가 삭제된다)

## 사용

    python3 scripts/restore_modality.py --before 01_input.txt --after final.md
    python3 scripts/restore_modality.py --before a.txt --after b.md --out b.md --json

`--out` 없으면 복원본을 stdout으로 낸다. 종료 코드는 항상 0 — 게이트가 아니다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_REFS = os.path.join(_ROOT, "skills", "humanize-korean", "references")
for _p in (_REFS, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import metrics_v2 as _m  # noqa: E402
from verify_gates import DEONTIC_RE, HEDGE_RE  # noqa: E402  (사전은 게이트와 단일 출처)

MODAL = {"당위": DEONTIC_RE, "추측": HEDGE_RE}

# 짝 문장이 "같은 문장의 다른 표현"인지 판정하는 하한. 정렬 아티팩트(엉뚱한 짝)를 거른다.
MIN_PAIR_SIM = 0.3
# 병합 판정 — 두 기준을 **모두** 만족할 때만 병합으로 본다.
#
# 처음에는 "원문 문장에 없던 내용어 2개 이상"만 봤는데, 실측에서 정상 윤문이 무더기로
# 걸렸다. "증가할 것으로 보인다는 견해가" → "늘어날 거라는 관측이"는 어휘를 셋이나 바꾸지만
# 병합이 아니다. 그 오탐 때문에 되돌려야 할 문장이 그대로 나갔다.
#
# 병합은 **문장이 길어지는** 현상이므로 길이비를 함께 본다. 더 정확한 신호는 정렬 구조다 —
# 병합되면 이웃 원문 문장이 짝을 잃고 gap(삭제)으로 남는다. 그쪽을 1차 기준으로 쓴다.
MERGE_FOREIGN_TOKENS = 3
MERGE_LEN_RATIO = 1.6

_WORD_RE = re.compile(r"[^\w]", re.UNICODE)


def _tokens(s: str) -> set[str]:
    return {t for t in (_WORD_RE.sub("", w) for w in s.split()) if t}


def _jaccard(a: str, b: str) -> float:
    A, B = _tokens(a), _tokens(b)
    if not A or not B:
        return 0.0
    inter = len(A & B)
    return inter / (len(A) + len(B) - inter)


def align(before: list[str], after: list[str]) -> list[tuple[str, str]]:
    """Needleman-Wunsch 문장 정렬. 1:1 짝과 gap(삽입·삭제)만 낸다."""
    n, m = len(before), len(after)
    gap = -0.4
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0] = score[i - 1][0] + gap
    for j in range(1, m + 1):
        score[0][j] = score[0][j - 1] + gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            score[i][j] = max(
                score[i - 1][j - 1] + _jaccard(before[i - 1], after[j - 1]),
                score[i - 1][j] + gap,
                score[i][j - 1] + gap,
            )
    pairs: list[tuple[str, str]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and abs(
            score[i][j] - (score[i - 1][j - 1] + _jaccard(before[i - 1], after[j - 1]))
        ) < 1e-9:
            pairs.append((before[i - 1], after[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and abs(score[i][j] - (score[i - 1][j] + gap)) < 1e-9:
            pairs.append((before[i - 1], ""))
            i -= 1
        else:
            pairs.append(("", after[j - 1]))
            j -= 1
    pairs.reverse()
    return pairs


def find_losses(before: str, after: str) -> list[dict]:
    """원문 문장의 서법이 짝 문장에서 사라진 경우를 찾는다.

    각 손실에 `neighbor_gap`을 함께 싣는다 — 바로 옆 원문 문장이 짝을 잃었다면
    이 문장이 그 내용을 흡수한 것(병합)일 수 있다는 표시다.
    """
    pairs = align(_m._split_sentences(before), _m._split_sentences(after))
    out: list[dict] = []
    for idx, (b, a) in enumerate(pairs):
        b, a = b.strip(), a.strip()
        # 삭제(짝 없음)는 서법 문제가 아니라 내용 소실 — 다른 축이 본다.
        if not b or not a:
            continue
        if _jaccard(b, a) < MIN_PAIR_SIM:
            continue
        neighbor_gap = any(
            pairs[j][0].strip() and not pairs[j][1].strip()
            for j in (idx - 1, idx + 1)
            if 0 <= j < len(pairs)
        )
        for kind, rx in MODAL.items():
            if rx.search(b) and not rx.search(a):
                out.append(
                    {"kind": kind, "before": b, "after": a, "neighbor_gap": neighbor_gap}
                )
                break
    return out


def restore(before: str, after: str) -> tuple[str, list[dict], list[dict]]:
    losses = find_losses(before, after)
    result = after
    restored: list[dict] = []
    skipped: list[dict] = []
    for loss in losses:
        if result.count(loss["after"]) != 1:
            skipped.append({**loss, "reason": "결과에서 유일하게 특정되지 않음"})
            continue
        foreign = [
            t for t in _tokens(loss["after"]) - _tokens(loss["before"]) if len(t) > 1
        ]
        longer = len(loss["after"]) >= len(loss["before"]) * MERGE_LEN_RATIO
        merged = loss.get("neighbor_gap") or (
            longer and len(foreign) >= MERGE_FOREIGN_TOKENS
        )
        if merged:
            skipped.append({**loss, "reason": "문장 병합 의심 — 되돌리면 다른 명제가 사라진다"})
            continue
        result = result.replace(loss["after"], loss["before"], 1)
        restored.append(loss)
    return result, restored, skipped


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="서법이 사라진 문장을 원문으로 되돌린다")
    ap.add_argument("--before", required=True, help="원문 파일")
    ap.add_argument("--after", required=True, help="윤문본 파일")
    ap.add_argument("--out", help="복원본을 쓸 파일(없으면 stdout)")
    ap.add_argument("--json", action="store_true", help="보고를 JSON으로 stderr에 출력")
    args = ap.parse_args(argv)

    with open(args.before, encoding="utf-8") as f:
        before = f.read()
    with open(args.after, encoding="utf-8") as f:
        after = f.read()

    result, restored, skipped = restore(before, after)

    report = {
        "restored": len(restored),
        "skipped": len(skipped),
        "details": {"restored": restored, "skipped": skipped},
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1), file=sys.stderr)
    else:
        print(f"[서법 복원] 복원 {len(restored)}문장 / 보류 {len(skipped)}문장", file=sys.stderr)
        for r in restored:
            print(f"  [{r['kind']}] {r['after'][:40]} → 원문", file=sys.stderr)
        for s in skipped:
            print(f"  (보류) {s['after'][:40]} — {s['reason']}", file=sys.stderr)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
