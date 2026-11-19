"""Mini NPU Simulator 핵심 기능 자동 검사 (표준 라이브러리만 사용)."""

import json
import unittest
from pathlib import Path

from main import analyze_case, compare_scores, generate_cross, generate_x, load_filters, mac


class TestMiniNPU(unittest.TestCase):
    def test_cross_vs_x(self):
        cross = generate_cross(3)
        x = generate_x(3)
        self.assertEqual(mac(x, cross), 1.0)
        self.assertEqual(mac(x, x), 5.0)
        self.assertEqual(compare_scores(1.0, 5.0), "B")

    def test_close_scores_undecided(self):
        self.assertEqual(compare_scores(1, 1 + 1e-10), "UNDECIDED")

    def test_invalid_shape(self):
        with self.assertRaises(ValueError):
            mac([[1, 0], [0, 1]], [[1, 0]])

    def test_sample_data(self):
        data_path = Path(__file__).with_name("data.json")
        data = json.loads(data_path.read_text(encoding="utf-8"))
        filters, errors = load_filters(data)
        self.assertEqual(errors, [])
        for case_id, case_data in data["patterns"].items():
            with self.subTest(case_id=case_id):
                result = analyze_case(case_id, case_data, filters)
                self.assertEqual(result["status"], "PASS", result["reason"])


if __name__ == "__main__":
    unittest.main()
