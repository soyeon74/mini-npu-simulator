"""Mini NPU Simulator 핵심 기능 자동 검사 (표준 라이브러리만 사용)."""

import json
import unittest
from pathlib import Path

from main import (
    analyze_case,
    compare_scores,
    flatten_matrix,
    generate_cross,
    generate_x,
    load_filters,
    mac,
    mac_flat,
    normalize_label,
)


class TestMiniNPU(unittest.TestCase):
    # [테스트 1] X 패턴의 점수와 승자 계산
    def test_cross_vs_x(self):
        cross = generate_cross(3)
        x = generate_x(3)
        self.assertEqual(mac(x, cross), 1.0)
        self.assertEqual(mac(x, x), 5.0)
        self.assertEqual(compare_scores(1.0, 5.0), "B")

    # [테스트 2] 매우 작은 점수 차이의 동점 판정
    def test_close_scores_undecided(self):
        self.assertEqual(compare_scores(1, 1 + 1e-10), "UNDECIDED")

    # [테스트 3] 행렬 크기 불일치 오류 처리
    def test_invalid_shape(self):
        with self.assertRaises(ValueError):
            mac([[1, 0], [0, 1]], [[1, 0]])

    # [테스트 4] 정상 학습용 8건 PASS와 가중치 데이터의 3 PASS/3 동점 FAIL을 각각 검증한다.
    def test_sample_data(self):
        # 기본 Cross/X 예제 8건은 별도로 보존해 항상 모두 PASS인지 확인한다.
        sample_path = Path(__file__).with_name("data_sample_8pass.json")
        sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
        sample_filters, errors = load_filters(sample_data)
        self.assertEqual(errors, [])
        self.assertEqual(len(sample_data["patterns"]), 8)
        for case_id, case_data in sample_data["patterns"].items():
            with self.subTest(dataset="sample", case_id=case_id):
                result = analyze_case(case_id, case_data, sample_filters)
                self.assertEqual(result["status"], "PASS", result["reason"])

        # 새 data.json은 의도적인 동점 사례를 포함한 별도 검증 시나리오이다.
        scenario_path = Path(__file__).with_name("data.json")
        scenario_data = json.loads(scenario_path.read_text(encoding="utf-8"))
        scenario_filters, errors = load_filters(scenario_data)
        self.assertEqual(errors, [])
        expected_status = {
            "size_5_1": "FAIL",
            "size_5_2": "PASS",
            "size_13_1": "PASS",
            "size_13_2": "FAIL",
            "size_25_1": "FAIL",
            "size_25_2": "PASS",
        }
        self.assertEqual(set(scenario_data["patterns"]), set(expected_status))
        for case_id, case_data in scenario_data["patterns"].items():
            with self.subTest(dataset="weighted", case_id=case_id):
                result = analyze_case(case_id, case_data, scenario_filters)
                self.assertEqual(result["status"], expected_status[case_id], result["reason"])
                if expected_status[case_id] == "FAIL":
                    self.assertEqual(result["decision"], "UNDECIDED")

    # [테스트 5] 2차원/1차원 MAC 결과 일치
    def test_flattened_mac_matches_original(self):
        for size in (3, 5, 13, 25):
            with self.subTest(size=size):
                cross = generate_cross(size)
                x_pattern = generate_x(size)
                self.assertEqual(
                    mac(cross, x_pattern),
                    mac_flat(flatten_matrix(cross), flatten_matrix(x_pattern)),
                )
                self.assertEqual(len(flatten_matrix(cross)), size * size)

    # [테스트 6] 생성된 Cross/X 패턴의 정답 판정
    def test_generator_recognizes_both_patterns(self):
        for size in (3, 5, 13, 25):
            with self.subTest(size=size):
                cross = generate_cross(size)
                x_pattern = generate_x(size)
                self.assertEqual(
                    compare_scores(mac(cross, cross), mac(cross, x_pattern), "Cross", "X"),
                    "Cross",
                )
                self.assertEqual(
                    compare_scores(mac(x_pattern, cross), mac(x_pattern, x_pattern), "Cross", "X"),
                    "X",
                )

    # [테스트 7] 1차원 길이 불일치 오류
    def test_flattened_mac_invalid_length(self):
        with self.assertRaises(ValueError):
            mac_flat([1, 0], [1])

    # [테스트 8] 잘못된 홀수 크기 입력 검증
    def test_generator_invalid_size(self):
        for size in (0, 2, 4, -1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                generate_cross(size)

    # [테스트 9] 라벨 표기 통일과 미지원 라벨 확인
    def test_label_normalization(self):
        self.assertEqual(normalize_label("+"), "Cross")
        self.assertEqual(normalize_label("cross"), "Cross")
        self.assertEqual(normalize_label("Cross"), "Cross")
        self.assertEqual(normalize_label("십자가"), "Cross")
        self.assertEqual(normalize_label("x"), "X")
        self.assertEqual(normalize_label(" X "), "X")
        self.assertIsNone(normalize_label("Circle"))

    # [테스트 10] EPSILON보다 작은 차이 및 큰 차이 비교
    def test_epsilon_boundary_behavior(self):
        self.assertEqual(compare_scores(1.0, 1.0 + 1e-10), "UNDECIDED")
        self.assertEqual(compare_scores(1.0, 1.0 + 1e-6), "B")


if __name__ == "__main__":
    unittest.main()
