"""서법 국소 복원기(scripts/restore_modality.py) 단위 테스트.

이 스크립트는 판정기가 아니라 **결과물을 바꾸는 변형기**다. 잘못 치환하면 게이트가
아니라 새 오류의 원인이 되므로, "고쳐야 할 때 고치는가"만큼 "애매하면 손대지 않는가"를
같은 비중으로 고정한다.
"""
from __future__ import annotations

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
import restore_modality as rm  # noqa: E402


class RestoreModalityTests(unittest.TestCase):
    def test_restores_hedge_flattened_to_assertion(self) -> None:
        """실측에서 반복된 유형 — 관측형 종결이 단정으로 바뀐 문장."""
        before = "이 수치는 이전 전망치보다 0.4%포인트 낮은 것으로 판단된다."
        after = "이 수치는 이전 전망치보다 0.4%포인트 낮은 수치다."
        out, restored, skipped = rm.restore(before, after)
        self.assertEqual(len(restored), 1, f"복원 안 됨: {skipped}")
        self.assertIn("낮은 것으로 판단된다", out)

    def test_restores_deontic_flattened_to_fact(self) -> None:
        """당위(필자가 요구한 것)가 이미 일어난 사실로 바뀐 문장."""
        before = "정부는 공유 플랫폼을 구축해야 한다."
        after = "정부는 공유 플랫폼을 구축한다."
        out, restored, _ = rm.restore(before, after)
        self.assertEqual(len(restored), 1)
        self.assertIn("구축해야 한다", out)

    def test_keeps_output_when_modality_preserved(self) -> None:
        """서법이 유지된 정상 윤문은 건드리지 않는다(형태만 바뀐 경우 포함)."""
        before = "초기 비용이 증가할 것으로 보인다."
        after = "초기 비용이 늘어날 듯하다."
        out, restored, _ = rm.restore(before, after)
        self.assertEqual(restored, [])
        self.assertEqual(out, after)

    def test_skips_when_sentences_merged(self) -> None:
        """병합 문장은 되돌리면 합쳐진 다른 명제가 삭제된다 — 손대지 않고 보류한다."""
        before = "정부는 재정 지출을 늘려야 한다."
        after = "정부는 재정 지출을 늘리고 세제도 함께 손질한다."
        out, restored, skipped = rm.restore(before, after)
        self.assertEqual(restored, [])
        self.assertEqual(out, after)
        self.assertEqual(len(skipped), 1)
        self.assertIn("병합", skipped[0]["reason"])

    def test_skips_when_target_not_unique(self) -> None:
        """같은 문장이 두 번 나오면 엉뚱한 쪽을 치환할 수 있다 — 보류한다."""
        sent_b = "내년 인건비 부담이 크게 늘어날 것으로 보인다."
        sent_a = "내년 인건비 부담이 크게 늘어난다."
        before = f"{sent_b} 중간 문단이다. {sent_b}"
        after = f"{sent_a} 중간 문단이다. {sent_a}"
        out, restored, skipped = rm.restore(before, after)
        self.assertEqual(restored, [])
        self.assertEqual(out, after)
        self.assertTrue(skipped)
        self.assertIn("유일", skipped[0]["reason"])

    def test_ignores_unrelated_sentence_pairs(self) -> None:
        """유사도가 낮은 짝은 정렬 아티팩트 — 서법 판정 대상이 아니다."""
        before = "규제안의 영향은 아직 단정하기 어렵다."
        after = "부산 북구의 인구는 계속 줄었다."
        _, restored, _ = rm.restore(before, after)
        self.assertEqual(restored, [])

    def test_deleted_sentence_is_not_a_modality_case(self) -> None:
        """문장이 통째로 사라진 것은 내용 소실 — 다른 축이 본다."""
        before = "비용이 늘어날 것으로 보인다. 통계는 분기마다 갱신된다."
        after = "통계는 분기마다 갱신된다."
        _, restored, _ = rm.restore(before, after)
        self.assertEqual(restored, [])


if __name__ == "__main__":
    unittest.main()
