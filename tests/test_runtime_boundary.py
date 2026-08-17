"""프로덕션 런타임이 tests/ 트리에 의존하지 않는지 검증 (#59).

배경: `scripts/verify_gates.py`(프로덕션 게이트)가 `tests/golden/checks.py` 를
런타임에 import 하고 있었다. 저장소 전체를 배포하는 Claude Code 설치에서는
동작하지만, 런타임 파일만 선별 배포하는 구조(포트·zip·심링크 부분 배포)에서는
**P3 golden 축이 통째로 죽는다**. 게이트가 조용히 한 축을 잃는 것이 가장 나쁘다.

checks.py 는 이름만 tests 아래 있었을 뿐 내용은 전부 프로덕션 검사 로직
(register·heading·footnote·number·quote)이라 `scripts/` 로 옮겼다.

이 테스트는 그 경계가 다시 무너지면 실패한다.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_SCRIPTS = _ROOT / "scripts"

# 프로덕션 런타임에 해당하는 스크립트(스킬이 Bash 로 직접 부르는 것들)
_RUNTIME_SCRIPTS = [
    "verify_gates.py",
    "verify_change_rate.py",
    "prepare_monolith_input.py",
    "reassemble_chunks.py",
    "sanitize_text.py",
    "checks.py",
]


class RuntimeBoundaryTests(unittest.TestCase):
    def test_runtime_scripts_do_not_reference_tests_tree(self) -> None:
        """런타임 스크립트 소스에 tests/ 경로 조립이 없어야 한다."""
        offenders: list[str] = []
        for name in _RUNTIME_SCRIPTS:
            p = _SCRIPTS / name
            if not p.is_file():
                continue
            src = p.read_text(encoding="utf-8")
            for lineno, line in enumerate(src.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue  # 주석의 이력 서술은 허용
                if '"tests"' in line or "'tests'" in line or "tests/golden" in line:
                    offenders.append(f"{name}:{lineno}: {stripped[:90]}")
        self.assertEqual(offenders, [], "런타임이 tests/ 를 참조함:\n" + "\n".join(offenders))

    def test_checks_lives_in_scripts(self) -> None:
        """checks.py 는 프로덕션 위치에 있어야 한다."""
        self.assertTrue((_SCRIPTS / "checks.py").is_file(), "scripts/checks.py 가 없음")
        self.assertFalse(
            (_ROOT / "tests" / "golden" / "checks.py").is_file(),
            "tests/golden/checks.py 가 되살아남 — 프로덕션 구현은 scripts/ 에 둔다",
        )

    def test_verify_gates_runs_without_tests_dir(self) -> None:
        """tests/ 를 뺀 선별 배포에서도 게이트 전 축이 동작해야 한다 (#59 핵심)."""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "scripts").mkdir()
            for f in _SCRIPTS.glob("*.py"):
                (d / "scripts" / f.name).write_bytes(f.read_bytes())
            refs_src = _ROOT / ".claude" / "skills" / "humanize-korean" / "references"
            refs_dst = d / ".claude" / "skills" / "humanize-korean" / "references"
            refs_dst.mkdir(parents=True)
            for f in refs_src.iterdir():
                if f.is_file():
                    (refs_dst / f.name).write_bytes(f.read_bytes())

            self.assertFalse((d / "tests").exists(), "tests/ 가 없어야 하는 조건")

            (d / "before.txt").write_text(
                "원문은 이러하다. 수치는 1,200명이다.", encoding="utf-8"
            )
            (d / "after.txt").write_text(
                "원문은 이렇다. 수치는 1,200명이다.", encoding="utf-8"
            )
            proc = subprocess.run(
                [sys.executable, "scripts/verify_gates.py", "--before", "before.txt",
                 "--after", "after.txt"],
                cwd=d, capture_output=True, text=True, timeout=120,
            )
            self.assertIn("[P3 golden]", proc.stdout, f"golden 축 누락\n{proc.stdout}\n{proc.stderr}")
            self.assertNotIn("ModuleNotFoundError", proc.stderr)
            self.assertIn(proc.returncode, (0, 1), f"예상치 못한 종료: {proc.returncode}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
