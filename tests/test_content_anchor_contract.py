"""핵심 내용 명사·개념어 보존 계약의 배포 경로 정합을 검증한다."""

from __future__ import annotations

import io
import os
import subprocess
import unittest
from unittest import mock

from tests import humanize_runner


_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(relative: str) -> str:
    with open(os.path.join(_ROOT, relative), encoding="utf-8") as f:
        return f.read()


class ContentAnchorContractTests(unittest.TestCase):
    def test_runtime_contracts_preserve_content_anchors(self) -> None:
        for path in (
            ".claude/skills/humanize-korean/SKILL.md",
            "agents/humanize-monolith.md",
            "agents/humanize-finalizer.md",
            ".claude/skills/humanize-korean/references/quick-rules.header.md",
            ".claude/skills/humanize-korean/references/quick-rules.footer.md",
        ):
            with self.subTest(path=path):
                text = _read(path)
                self.assertIn("핵심 내용 명사·개념어", text)
                self.assertIn("원형", text)

    def test_live_prompt_reinforces_anchor_and_overedit_guards(self) -> None:
        prompt = humanize_runner._prompt(
            "패러다임을 설명합니다.",
            strict=False,
            protected_tokens=["패러다임"],
            max_change_rate=0.50,
        )
        self.assertIn("핵심 내용 명사·개념어", prompt)
        self.assertIn("문자 단위 변경률은 50% 이하", prompt)
        self.assertIn("이미 자연스러운 구간은 손대지", prompt)
        self.assertIn('보호 토큰은 결과에 정확히 그대로 남겨: ["패러다임"]', prompt)

    @mock.patch.object(humanize_runner, "CLAUDE_BIN", "/usr/bin/claude")
    @mock.patch.object(humanize_runner.subprocess, "run")
    def test_live_runner_retries_once_after_gate_violation(self, run: mock.Mock) -> None:
        original = "패러다임을 설명합니다."
        run.side_effect = [
            subprocess.CompletedProcess(
                [], 0, stdout="<<<H>>>완전히 다른 글입니다.<<</H>>>", stderr=""
            ),
            subprocess.CompletedProcess(
                [], 0, stdout=f"<<<H>>>{original}<<</H>>>", stderr=""
            ),
        ]

        with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            result = humanize_runner.run_humanize(
                original,
                protected_tokens=["패러다임"],
                max_change_rate=0.10,
            )

        self.assertEqual(result, original)
        self.assertEqual(run.call_count, 2)
        retry_log = stderr.getvalue()
        self.assertIn("retry 1/1 after gate violation", retry_log)
        self.assertIn("보호 토큰 유실", retry_log)
        self.assertIn("변경률", retry_log)
        retry_prompt = run.call_args_list[1].args[0][2]
        self.assertIn("직전 시도는", retry_prompt)
        self.assertIn("보호 토큰 유실", retry_prompt)
        self.assertIn("변경률", retry_prompt)


if __name__ == "__main__":
    unittest.main()
