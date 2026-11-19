import json
import re
import time
from pathlib import Path

EPSILON = 1e-9
PERF_REPEAT = 10
DATA_FILE = "data.json"


def print_title(title):
    print("\n" + "#" + "-" * 40)
    print(f"# {title}")
    print("#" + "-" * 40)


def normalize_label(value):
    """외부 표현을 프로그램 내부 표준 라벨 Cross / X 로 변환한다."""
    if value is None:
        return None

    text = str(value).strip().lower()

    mapping = {
        "+": "Cross",
        "cross": "Cross",
        "십자가": "Cross",
        "x": "X",
    }
    return mapping.get(text)


def validate_matrix(matrix, expected_size=None):
    """2차원 정방행렬 여부와 숫자형 데이터 여부를 검사한다."""
    if not isinstance(matrix, list) or not matrix:
        return False, "2차원 배열이 아닙니다."

    size = len(matrix)

    if expected_size is not None and size != expected_size:
        return False, f"행 개수 불일치: 예상 {expected_size}, 실제 {size}"

    for row_index, row in enumerate(matrix, start=1):
        if not isinstance(row, list):
            return False, f"{row_index}번째 행이 배열이 아닙니다."

        if len(row) != size:
            return False, (
                f"정방행렬이 아닙니다: {row_index}번째 행의 열 개수 "
                f"{len(row)}, 행 개수 {size}"
            )

        if expected_size is not None and len(row) != expected_size:
            return False, (
                f"{row_index}번째 행의 열 개수 불일치: "
                f"예상 {expected_size}, 실제 {len(row)}"
            )

        for value in row:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"{row_index}번째 행에 숫자가 아닌 값이 있습니다."

    return True, ""


def mac(pattern, filter_matrix):
    """
    Multiply-Accumulate.
    같은 위치의 값을 곱한 뒤 모두 더한다.
    외부 라이브러리를 사용하지 않고 반복문으로 직접 구현한다.
    """
    if len(pattern) != len(filter_matrix):
        raise ValueError("패턴과 필터의 행 개수가 다릅니다.")

    total = 0.0

    for i in range(len(pattern)):
        if len(pattern[i]) != len(filter_matrix[i]):
            raise ValueError("패턴과 필터의 열 개수가 다릅니다.")

        for j in range(len(pattern[i])):
            total += pattern[i][j] * filter_matrix[i][j]

    return total


def flatten_matrix(matrix):
    """2차원 행렬을 행 순서대로 1차원 리스트로 바꾼다."""
    return [value for row in matrix for value in row]


def mac_flat(flat_pattern, flat_filter):
    """1차원 배열에서 MAC 연산을 직접 반복하여 계산한다."""
    if len(flat_pattern) != len(flat_filter):
        raise ValueError("1차원 패턴과 필터 길이가 다릅니다.")

    total = 0.0
    for index in range(len(flat_pattern)):
        total += flat_pattern[index] * flat_filter[index]
    return total


def compare_scores(score_a, score_b, label_a="A", label_b="B"):
    """epsilon 기반으로 두 점수를 비교한다."""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b


def input_matrix(name, size=3):
    """사용자가 올바른 N×N 행렬을 입력할 때까지 재입력을 받는다."""
    while True:
        print(f"\n{name} ({size}줄 입력, 공백 구분)")

        matrix = []
        error = None

        for row_no in range(1, size + 1):
            raw = input(f"{row_no}행: ").strip()
            parts = raw.split()

            if len(parts) != size:
                error = (
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                break

            try:
                row = [float(value) for value in parts]
            except ValueError:
                error = "입력 형식 오류: 숫자만 입력하세요."
                break

            matrix.append(row)

        if error:
            print(error)
            print("해당 행렬을 처음부터 다시 입력해 주세요.")
            continue

        print(f"✓ {name} 저장 완료")
        return matrix


def measure_mac(pattern, filter_matrix, repeat=PERF_REPEAT):
    """I/O를 제외하고 MAC 함수 호출 구간만 반복 측정한다."""
    elapsed = []

    for _ in range(repeat):
        start = time.perf_counter()
        mac(pattern, filter_matrix)
        end = time.perf_counter()
        elapsed.append((end - start) * 1000.0)

    return sum(elapsed) / len(elapsed)


def measure_call(operation, repeat=PERF_REPEAT):
    """화면 출력과 파일 읽기를 제외하고 호출 시간을 반복 측정한다."""
    elapsed = []
    for _ in range(repeat):
        start = time.perf_counter()
        operation()
        elapsed.append((time.perf_counter() - start) * 1000.0)
    return sum(elapsed) / len(elapsed)


def generate_cross(size):
    """성능 측정용 Cross 패턴을 생성한다."""
    if not isinstance(size, int) or isinstance(size, bool) or size < 3 or size % 2 == 0:
        raise ValueError("크기는 3 이상의 홀수여야 합니다.")
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    mid = size // 2

    for i in range(size):
        matrix[mid][i] = 1.0
        matrix[i][mid] = 1.0

    return matrix


def generate_x(size):
    """성능 측정용 X 패턴을 생성한다."""
    if not isinstance(size, int) or isinstance(size, bool) or size < 3 or size % 2 == 0:
        raise ValueError("크기는 3 이상의 홀수여야 합니다.")
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    for i in range(size):
        matrix[i][i] = 1.0
        matrix[i][size - 1 - i] = 1.0

    return matrix


def print_performance_table(sizes, filters_by_size=None):
    print_title(f"[성능 분석] 평균/{PERF_REPEAT}회")
    print(f"{'크기':<10}{'평균 시간(ms)':>16}{'연산 횟수(N²)':>18}")
    print("-" * 44)

    for size in sizes:
        pattern = generate_cross(size)

        filter_matrix = None
        if filters_by_size and size in filters_by_size:
            filter_matrix = filters_by_size[size].get("Cross")

        if filter_matrix is None:
            filter_matrix = generate_cross(size)

        avg_ms = measure_mac(pattern, filter_matrix)
        print(f"{size}×{size:<7}{avg_ms:>16.6f}{size * size:>18}")


def print_matrix(matrix):
    for row in matrix:
        print(" ".join(f"{value:g}" for value in row))


def run_generator_mode():
    """보너스: 생성한 패턴을 즉시 판정하고 MAC 속도도 확인한다."""
    raw = input("생성할 크기 N (3~25의 홀수, 예: 5): ").strip()
    try:
        size = int(raw)
        if size < 3 or size > 25 or size % 2 == 0:
            raise ValueError
    except ValueError:
        print("입력 오류: 3부터 25까지의 홀수를 입력하세요.")
        return

    cross = generate_cross(size)
    x_pattern = generate_x(size)
    print_title(f"[보너스] {size}×{size} 패턴 자동 생성")
    print("Cross 패턴:")
    print_matrix(cross)
    print("X 패턴:")
    print_matrix(x_pattern)

    print("\n생성 패턴 자체 검증:")
    for name, pattern in (("Cross", cross), ("X", x_pattern)):
        cross_score = mac(pattern, cross)
        x_score = mac(pattern, x_pattern)
        decision = compare_scores(cross_score, x_score, "Cross", "X")
        print(f"{name}: Cross={cross_score:g}, X={x_score:g}, 판정={decision}")
    print_performance_table([size])


def run_optimization_mode():
    """보너스: 같은 데이터와 반복 횟수로 2차원/1차원 MAC를 비교한다."""
    print_title(f"[보너스] 2차원과 1차원 MAC 비교 (각 {PERF_REPEAT}회)")
    print("배열 변환 시간은 제외하고 MAC 계산 함수만 측정합니다.")
    print(f"{'크기':<10}{'2차원(ms)':>15}{'1차원(ms)':>15}{'점수 일치':>12}")
    print("-" * 52)

    for size in (3, 5, 13, 25):
        pattern = generate_cross(size)
        filter_matrix = generate_x(size)
        flat_pattern = flatten_matrix(pattern)
        flat_filter = flatten_matrix(filter_matrix)

        original_score = mac(pattern, filter_matrix)
        flat_score = mac_flat(flat_pattern, flat_filter)
        matches = abs(original_score - flat_score) < EPSILON
        average_2d = measure_call(lambda: mac(pattern, filter_matrix))
        average_1d = measure_call(lambda: mac_flat(flat_pattern, flat_filter))
        print(f"{size}×{size:<7}{average_2d:>15.6f}{average_1d:>15.6f}{'예' if matches else '아니요':>12}")

    print("※ 연산 속도 우열은 실행 환경에 따라 달라집니다. 1차원 변환 비용은 별도입니다.")


def run_manual_mode():
    print_title("[1] 필터 입력")
    filter_a = input_matrix("필터 A", 3)
    filter_b = input_matrix("필터 B", 3)

    print_title("[2] 패턴 입력")
    pattern = input_matrix("패턴", 3)

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    decision = compare_scores(score_a, score_b, "A", "B")

    elapsed = []
    for _ in range(PERF_REPEAT):
        start = time.perf_counter()
        mac(pattern, filter_a)
        mac(pattern, filter_b)
        end = time.perf_counter()
        elapsed.append((end - start) * 1000.0)
    avg_ms = sum(elapsed) / len(elapsed)

    print_title("[3] MAC 결과")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{PERF_REPEAT}회): {avg_ms:.6f} ms")

    if decision == "UNDECIDED":
        print(
            f"판정: 판정 불가 "
            f"(|A-B| < {EPSILON:g}, 차이={abs(score_a-score_b):.16g})"
        )
    else:
        print(f"판정: {decision}")

    print_performance_table([3])


def extract_size_from_key(key):
    match = re.search(r"size_(\d+)", str(key))
    if not match:
        return None
    return int(match.group(1))


def parse_filter_pair(filter_block, size):
    if not isinstance(filter_block, dict):
        return None, f"size_{size} 필터 데이터가 객체(dict)가 아닙니다."

    candidate = filter_block.get("filters", filter_block)

    if not isinstance(candidate, dict):
        return None, f"size_{size} 필터 내부 구조가 올바르지 않습니다."

    result = {}

    for raw_label, matrix in candidate.items():
        standard = normalize_label(raw_label)
        if standard in ("Cross", "X"):
            result[standard] = matrix

    missing = [label for label in ("Cross", "X") if label not in result]
    if missing:
        return None, f"필터 누락: {', '.join(missing)}"

    for label, matrix in result.items():
        valid, reason = validate_matrix(matrix, size)
        if not valid:
            return None, f"{label} 필터 오류: {reason}"

    return result, ""


def load_filters(data):
    filters_root = data.get("filters")

    if not isinstance(filters_root, dict):
        raise ValueError("data.json의 'filters'가 객체(dict)가 아닙니다.")

    filters_by_size = {}
    errors = []

    for key, block in filters_root.items():
        size = extract_size_from_key(key)

        if size is None:
            errors.append(f"{key}: 필터 키에서 크기 N을 추출할 수 없습니다.")
            continue

        pair, reason = parse_filter_pair(block, size)
        if pair is None:
            errors.append(f"{key}: {reason}")
            continue

        filters_by_size[size] = pair
        print(f"✓ size_{size:<2} 필터 로드 완료 (Cross, X)")

    return filters_by_size, errors


def iter_patterns(patterns_root):
    if not isinstance(patterns_root, dict):
        return []

    return list(patterns_root.items())


def analyze_case(case_id, case_data, filters_by_size):
    size = extract_size_from_key(case_id)

    if size is None:
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": "케이스 키에서 크기 N을 추출할 수 없음",
        }

    if size not in filters_by_size:
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": f"size_{size}에 대응하는 정상 필터가 없음",
        }

    if not isinstance(case_data, dict):
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": "패턴 데이터가 객체(dict)가 아님",
        }

    pattern = case_data.get("input")
    expected_raw = case_data.get("expected")

    valid, reason = validate_matrix(pattern, size)
    if not valid:
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": f"패턴 크기/스키마 오류: {reason}",
        }

    expected = normalize_label(expected_raw)
    if expected not in ("Cross", "X"):
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": f"expected 라벨 오류: {expected_raw!r}",
        }

    cross_filter = filters_by_size[size]["Cross"]
    x_filter = filters_by_size[size]["X"]

    cross_score = mac(pattern, cross_filter)
    x_score = mac(pattern, x_filter)
    decision = compare_scores(cross_score, x_score, "Cross", "X")

    passed = decision == expected

    if passed:
        reason = ""
    elif decision == "UNDECIDED":
        reason = (
            f"동점 규칙: |Cross-X| < {EPSILON:g} 이므로 "
            f"UNDECIDED, expected={expected}"
        )
    else:
        reason = f"판정={decision}, expected={expected}"

    return {
        "id": case_id,
        "size": size,
        "cross_score": cross_score,
        "x_score": x_score,
        "decision": decision,
        "expected": expected,
        "status": "PASS" if passed else "FAIL",
        "reason": reason,
    }


def run_json_mode():
    path = Path(DATA_FILE)

    if not path.exists():
        print(f"\n오류: 현재 폴더에서 {DATA_FILE}을 찾을 수 없습니다.")
        print(f"확인 위치: {path.resolve()}")
        return

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        print(f"\nJSON 형식 오류: {exc}")
        return
    except OSError as exc:
        print(f"\n파일 읽기 오류: {exc}")
        return

    if not isinstance(data, dict):
        print("\n오류: data.json 최상위 구조는 객체(dict)여야 합니다.")
        return

    print_title("[1] 필터 로드")

    try:
        filters_by_size, filter_errors = load_filters(data)
    except ValueError as exc:
        print(f"필터 스키마 오류: {exc}")
        return

    for error in filter_errors:
        print(f"✗ {error}")

    patterns_root = data.get("patterns")
    pattern_items = iter_patterns(patterns_root)

    if not pattern_items:
        print("\n오류: 분석할 patterns 항목이 없습니다.")
        return

    print_title("[2] 패턴 분석 (라벨 정규화 적용)")

    results = []

    for case_id, case_data in pattern_items:
        result = analyze_case(case_id, case_data, filters_by_size)
        results.append(result)

        print(f"\n--- {case_id} ---")

        if "cross_score" in result:
            print(f"Cross 점수: {result['cross_score']}")
            print(f"X 점수: {result['x_score']}")
            print(
                f"판정: {result['decision']} | "
                f"expected: {result['expected']} | "
                f"{result['status']}"
            )
            if result["reason"]:
                print(f"사유: {result['reason']}")
        else:
            print(f"판정 불가 | {result['status']}")
            print(f"사유: {result['reason']}")

    sizes = [3]
    for size in (5, 13, 25):
        if size not in sizes:
            sizes.append(size)

    print_performance_table(sizes, filters_by_size)

    print_title("[4] 결과 요약")

    total = len(results)
    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = total - passed

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed:
        print("\n실패 케이스:")
        for result in results:
            if result["status"] == "FAIL":
                print(f"- {result['id']}: {result['reason']}")
    else:
        print("\n실패 케이스 없음")
        print("라벨 정규화와 epsilon 기반 점수 비교 정책이 정상 적용되었습니다.")


def main():
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 패턴 자동 생성 (보너스)")
        print("4. 1차원 최적화 비교 (보너스)")
        print("0. 종료")

        choice = input("선택: ").strip()

        if choice == "1":
            run_manual_mode()
        elif choice == "2":
            run_json_mode()
        elif choice == "3":
            run_generator_mode()
        elif choice == "4":
            run_optimization_mode()
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("입력 오류: 0, 1, 2, 3, 4 중 하나를 입력하세요.")


if __name__ == "__main__":
    main()
