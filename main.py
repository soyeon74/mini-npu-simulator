import json
import re
import time
from pathlib import Path

# 두 점수 차이가 이 값보다 작으면 동점으로 처리하는 허용오차다.
EPSILON = 1e-9
# 반복 시간을 측정할 때 실행하는 횟수다.
PERF_REPEAT = 10
# JSON 분석 모드에서 읽을 파일 이름이다.
DATA_FILE = "data.json"


# [함수 해설] 콘솔 제목과 구분선을 출력한다. 인자는 제목 문자열이며 반환값은 없다.
def print_title(title):
    print("\n" + "#" + "-" * 40)
    print(f"# {title}")
    print("#" + "-" * 40)


# [함수 해설] 외부의 '+', 'cross', 'x' 등의 표현을 Cross/X 표준 이름으로 바꾼다. 미지원 값은 None.
def normalize_label(value):
    """외부 표현을 프로그램 내부 표준 라벨 Cross / X 로 변환한다."""
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if value is None:
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return None

    # str은 문자열 변환, strip은 양끝 공백 제거, lower는 소문자 변환이다.
    text = str(value).strip().lower()

    # 서로 다른 입력 표현을 같은 표준 라벨로 통일하는 딕셔너리다.
    mapping = {
        "+": "Cross",
        "cross": "Cross",
        "십자가": "Cross",
        "x": "X",
    }
    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return mapping.get(text)


# [함수 해설] 입력 행렬이 숫자형 N×N 구조인지 확인한다. (성공여부, 오류문구)를 반환한다.
def validate_matrix(matrix, expected_size=None):
    """2차원 정방행렬 여부와 숫자형 데이터 여부를 검사한다."""
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(matrix, list) or not matrix:
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return False, "2차원 배열이 아닙니다."

    size = len(matrix)

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if expected_size is not None and size != expected_size:
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return False, f"행 개수 불일치: 예상 {expected_size}, 실제 {size}"

    # enumerate는 1부터 시작하는 행 번호와 해당 행의 값을 함께 준다.
    for row_index, row in enumerate(matrix, start=1):
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if not isinstance(row, list):
            # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
            return False, f"{row_index}번째 행이 배열이 아닙니다."

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if len(row) != size:
            # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
            return False, (
                f"정방행렬이 아닙니다: {row_index}번째 행의 열 개수 "
                f"{len(row)}, 행 개수 {size}"
            )

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if expected_size is not None and len(row) != expected_size:
            # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
            return False, (
                f"{row_index}번째 행의 열 개수 불일치: "
                f"예상 {expected_size}, 실제 {len(row)}"
            )

        # 각 행의 값을 하나씩 꺼내 숫자 타입인지 확인한다.
        for value in row:
            # if 조건이 참일 때만 아래 코드를 수행한다.
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
                return False, f"{row_index}번째 행에 숫자가 아닌 값이 있습니다."

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return True, ""


# [함수 해설] 동일 위치 숫자를 곱하고 모두 더하는 MAC 함수를 2차원 이중 for문으로 실행한다. 숫자 합계 반환.
def mac(pattern, filter_matrix):
    """
    Multiply-Accumulate.
    같은 위치의 값을 곱한 뒤 모두 더한다.
    외부 라이브러리를 사용하지 않고 반복문으로 직접 구현한다.
    """
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if len(pattern) != len(filter_matrix):
        # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
        raise ValueError("패턴과 필터의 행 개수가 다릅니다.")

    # 곱셈 결과를 누적할 합계 변수를 0으로 초기화한다.
    total = 0.0

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for i in range(len(pattern)):
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if len(pattern[i]) != len(filter_matrix[i]):
            # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
            raise ValueError("패턴과 필터의 열 개수가 다릅니다.")

        # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
        for j in range(len(pattern[i])):
            # [행 i][열 j]의 같은 위치 값을 곱한 뒤 누적합에 더한다.
            total += pattern[i][j] * filter_matrix[i][j]

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return total


# [함수 해설] 2차원 리스트를 행 순서대로 펼친 새로운 1차원 리스트를 반환한다.
def flatten_matrix(matrix):
    """2차원 행렬을 행 순서대로 1차원 리스트로 바꾼다."""
    # 리스트 컴프리헨션으로 각 행의 숫자를 순서대로 한 줄에 펼친다.
    return [value for row in matrix for value in row]


# [함수 해설] 1차원으로 펼친 패턴과 필터의 같은 위치를 곱해 더한 점수를 반환한다.
def mac_flat(flat_pattern, flat_filter):
    """1차원 배열에서 MAC 연산을 직접 반복하여 계산한다."""
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if len(flat_pattern) != len(flat_filter):
        # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
        raise ValueError("1차원 패턴과 필터 길이가 다릅니다.")

    # 곱셈 결과를 누적할 합계 변수를 0으로 초기화한다.
    total = 0.0
    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for index in range(len(flat_pattern)):
        # 펼친 1차원 리스트의 동일 인덱스 값들을 곱해 누적한다.
        total += flat_pattern[index] * flat_filter[index]
    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return total


# [함수 해설] 두 점수의 차이를 EPSILON과 비교하고 승자 라벨이나 UNDECIDED를 반환한다.
def compare_scores(score_a, score_b, label_a="A", label_b="B"):
    """epsilon 기반으로 두 점수를 비교한다."""
    # abs는 절댓값이다. 점수의 차이가 충분히 작으면 동점 처리한다.
    if abs(score_a - score_b) < EPSILON:
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return "UNDECIDED"
    # A 점수가 더 높으면 A 라벨, 아니면 B 라벨을 반환하는 조건식이다.
    return label_a if score_a > score_b else label_b


# [함수 해설] 키보드로 size개 행을 입력받고 형식이 틀리면 처음부터 다시 입력하도록 한다.
def input_matrix(name, size=3):
    """사용자가 올바른 N×N 행렬을 입력할 때까지 재입력을 받는다."""
    # 조건이 유지되는 동안 계속 반복하며 break 또는 return으로 빠져나온다.
    while True:
        print(f"\n{name} ({size}줄 입력, 공백 구분)")

        matrix = []
        error = None

        # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
        for row_no in range(1, size + 1):
            raw = input(f"{row_no}행: ").strip()
            # 공백을 기준으로 사용자 입력 문자열을 숫자 후보들로 나눈다.
            parts = raw.split()

            # if 조건이 참일 때만 아래 코드를 수행한다.
            if len(parts) != size:
                error = (
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                    "공백으로 구분해 입력하세요."
                )
                # 가장 가까운 반복문을 종료한다.
                break

            # 오류가 발생할 수 있는 동작을 시도한다.
            try:
                # 공백으로 분리된 문자열을 숫자(float)로 변환한다.
                row = [float(value) for value in parts]
            # 발생한 오류를 잡아 사용자에게 설명하고 중단을 방지한다.
            except ValueError:
                error = "입력 형식 오류: 숫자만 입력하세요."
                # 가장 가까운 반복문을 종료한다.
                break

            matrix.append(row)

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if error:
            print(error)
            print("해당 행렬을 처음부터 다시 입력해 주세요.")
            # 현재 반복을 건너뛰고 다음 반복으로 진행한다.
            continue

        print(f"✓ {name} 저장 완료")
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return matrix


# [함수 해설] MAC 호출 시간만 지정 횟수 반복 측정하고 평균 밀리초를 반환한다.
def measure_mac(pattern, filter_matrix, repeat=PERF_REPEAT):
    """I/O를 제외하고 MAC 함수 호출 구간만 반복 측정한다."""
    elapsed = []

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for _ in range(repeat):
        start = time.perf_counter()
        mac(pattern, filter_matrix)
        end = time.perf_counter()
        # 측정한 초에 1000을 곱해 밀리초(ms)로 저장한다.
        elapsed.append((end - start) * 1000.0)

    # 반복 측정한 시간을 모두 더해 횟수로 나누어 평균을 구한다.
    return sum(elapsed) / len(elapsed)


# [함수 해설] 전달받은 함수의 실행 시간만 반복 측정해 평균 밀리초를 반환한다.
def measure_call(operation, repeat=PERF_REPEAT):
    """화면 출력과 파일 읽기를 제외하고 호출 시간을 반복 측정한다."""
    elapsed = []
    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for _ in range(repeat):
        start = time.perf_counter()
        operation()
        # 측정한 초에 1000을 곱해 밀리초(ms)로 저장한다.
        elapsed.append((time.perf_counter() - start) * 1000.0)
    # 반복 측정한 시간을 모두 더해 횟수로 나누어 평균을 구한다.
    return sum(elapsed) / len(elapsed)


# [함수 해설] 홀수 크기의 0 배열에서 가운데 행과 열을 1로 설정해 십자가를 만든다.
def generate_cross(size):
    """성능 측정용 Cross 패턴을 생성한다."""
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(size, int) or isinstance(size, bool) or size < 3 or size % 2 == 0:
        # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
        raise ValueError("크기는 3 이상의 홀수여야 합니다.")
    # 안쪽 for로 열, 바깥 for로 행을 만들어 0으로 채운 정사각 배열을 생성한다.
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    # //는 몫을 구한다. 크기가 5이면 가운데 인덱스는 2다.
    mid = size // 2

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for i in range(size):
        # 행을 가운데(mid)로 고정하고 열을 i로 이동하여 가로줄을 채운다.
        matrix[mid][i] = 1.0
        # 열을 가운데(mid)로 고정하고 행을 i로 이동하여 세로줄을 채운다.
        matrix[i][mid] = 1.0

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return matrix


# [함수 해설] 홀수 크기의 0 배열에서 두 대각선을 1로 설정해 X를 만든다.
def generate_x(size):
    """성능 측정용 X 패턴을 생성한다."""
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(size, int) or isinstance(size, bool) or size < 3 or size % 2 == 0:
        # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
        raise ValueError("크기는 3 이상의 홀수여야 합니다.")
    # 안쪽 for로 열, 바깥 for로 행을 만들어 0으로 채운 정사각 배열을 생성한다.
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for i in range(size):
        # 같은 행·열 번호를 사용해 왼쪽 위에서 오른쪽 아래 대각선을 채운다.
        matrix[i][i] = 1.0
        # 행 i는 증가하고 열 size-1-i는 감소하므로 반대 대각선을 채운다.
        matrix[i][size - 1 - i] = 1.0

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return matrix


# [함수 해설] 크기별 평균 MAC 시간과 N² 계산 위치 개수를 출력한다.
def print_performance_table(sizes, filters_by_size=None):
    print_title(f"[성능 분석] 평균/{PERF_REPEAT}회")
    print(f"{'크기':<10}{'평균 시간(ms)':>16}{'연산 횟수(N²)':>18}")
    print("-" * 44)

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for size in sizes:
        pattern = generate_cross(size)

        filter_matrix = None
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if filters_by_size and size in filters_by_size:
            filter_matrix = filters_by_size[size].get("Cross")

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if filter_matrix is None:
            filter_matrix = generate_cross(size)

        avg_ms = measure_mac(pattern, filter_matrix)
        print(f"{size}×{size:<7}{avg_ms:>16.6f}{size * size:>18}")


# [함수 해설] 행렬을 행 단위로 화면에 출력한다.
def print_matrix(matrix):
    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for row in matrix:
        print(" ".join(f"{value:g}" for value in row))


# [함수 해설] 메뉴 3: 패턴 생성, 출력, MAC 판정과 성능 측정을 수행한다.
def run_generator_mode():
    """보너스: 생성한 패턴을 즉시 판정하고 MAC 속도도 확인한다."""
    raw = input("생성할 크기 N (3~25의 홀수, 예: 5): ").strip()
    # 오류가 발생할 수 있는 동작을 시도한다.
    try:
        # 사용자가 입력한 문자열을 정수로 바꾼다. 숫자가 아니면 오류가 발생한다.
        size = int(raw)
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if size < 3 or size > 25 or size % 2 == 0:
            # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
            raise ValueError
    # 발생한 오류를 잡아 사용자에게 설명하고 중단을 방지한다.
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
    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for name, pattern in (("Cross", cross), ("X", x_pattern)):
        cross_score = mac(pattern, cross)
        x_score = mac(pattern, x_pattern)
        decision = compare_scores(cross_score, x_score, "Cross", "X")
        print(f"{name}: Cross={cross_score:g}, X={x_score:g}, 판정={decision}")
    print_performance_table([size])


# [함수 해설] 메뉴 4: 2차원과 1차원 MAC 점수와 평균 연산 시간을 비교한다. 변환 시간은 제외한다.
def run_optimization_mode():
    """보너스: 같은 데이터와 반복 횟수로 2차원/1차원 MAC를 비교한다."""
    print_title(f"[보너스] 2차원과 1차원 MAC 비교 (각 {PERF_REPEAT}회)")
    print("배열 변환 시간은 제외하고 MAC 계산 함수만 측정합니다.")
    print(f"{'크기':<10}{'2차원(ms)':>15}{'1차원(ms)':>15}{'점수 일치':>12}")
    print("-" * 52)

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for size in (3, 5, 13, 25):
        pattern = generate_cross(size)
        filter_matrix = generate_x(size)
        # 행렬의 각 행을 순서대로 펼쳐 새 1차원 리스트를 준비한다.
        flat_pattern = flatten_matrix(pattern)
        flat_filter = flatten_matrix(filter_matrix)

        original_score = mac(pattern, filter_matrix)
        flat_score = mac_flat(flat_pattern, flat_filter)
        matches = abs(original_score - flat_score) < EPSILON
        # lambda로 2차원 MAC 연산을 함수 형태로 전달하여 시간만 측정한다.
        average_2d = measure_call(lambda: mac(pattern, filter_matrix))
        # 1차원 MAC 연산의 시간만 측정하며 변환 시간은 제외한다.
        average_1d = measure_call(lambda: mac_flat(flat_pattern, flat_filter))
        print(f"{size}×{size:<7}{average_2d:>15.6f}{average_1d:>15.6f}{'예' if matches else '아니요':>12}")

    print("※ 연산 속도 우열은 실행 환경에 따라 달라집니다. 1차원 변환 비용은 별도입니다.")


# [함수 해설] 메뉴 1: 사용자가 필터 A·B와 패턴을 입력하여 점수와 판정을 확인한다.
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
    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for _ in range(PERF_REPEAT):
        start = time.perf_counter()
        mac(pattern, filter_a)
        mac(pattern, filter_b)
        end = time.perf_counter()
        # 측정한 초에 1000을 곱해 밀리초(ms)로 저장한다.
        elapsed.append((end - start) * 1000.0)
    avg_ms = sum(elapsed) / len(elapsed)

    print_title("[3] MAC 결과")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{PERF_REPEAT}회): {avg_ms:.6f} ms")

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if decision == "UNDECIDED":
        print(
            f"판정: 판정 불가 "
            f"(|A-B| < {EPSILON:g}, 차이={abs(score_a-score_b):.16g})"
        )
    # 앞 조건이 모두 거짓일 때 실행한다.
    else:
        print(f"판정: {decision}")

    print_performance_table([3])


# [함수 해설] size_13_1 같은 문자열의 size_ 뒤 숫자 13을 추출한다.
def extract_size_from_key(key):
    # 정규표현식의 \d+는 숫자 한 자리 이상을 뜻한다.
    match = re.search(r"size_(\d+)", str(key))
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not match:
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return None
    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return int(match.group(1))


# [함수 해설] JSON의 크기별 Cross/X 필터를 표준화하고 형태를 검증한다.
def parse_filter_pair(filter_block, size):
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(filter_block, dict):
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return None, f"size_{size} 필터 데이터가 객체(dict)가 아닙니다."

    # 내부 filters가 있으면 사용하고 없으면 원래 필터 블록을 사용한다.
    candidate = filter_block.get("filters", filter_block)

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(candidate, dict):
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return None, f"size_{size} 필터 내부 구조가 올바르지 않습니다."

    result = {}

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for raw_label, matrix in candidate.items():
        standard = normalize_label(raw_label)
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if standard in ("Cross", "X"):
            result[standard] = matrix

    # Cross와 X 중 누락된 라벨을 리스트로 모은다.
    missing = [label for label in ("Cross", "X") if label not in result]
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if missing:
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return None, f"필터 누락: {', '.join(missing)}"

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for label, matrix in result.items():
        valid, reason = validate_matrix(matrix, size)
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if not valid:
            # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
            return None, f"{label} 필터 오류: {reason}"

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return result, ""


# [함수 해설] JSON에서 크기별 필터를 로드해 정상 필터와 오류 목록을 반환한다.
def load_filters(data):
    filters_root = data.get("filters")

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(filters_root, dict):
        # 잘못된 입력을 발견해 ValueError 오류를 발생시킨다.
        raise ValueError("data.json의 'filters'가 객체(dict)가 아닙니다.")

    filters_by_size = {}
    errors = []

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for key, block in filters_root.items():
        size = extract_size_from_key(key)

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if size is None:
            errors.append(f"{key}: 필터 키에서 크기 N을 추출할 수 없습니다.")
            # 현재 반복을 건너뛰고 다음 반복으로 진행한다.
            continue

        pair, reason = parse_filter_pair(block, size)
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if pair is None:
            errors.append(f"{key}: {reason}")
            # 현재 반복을 건너뛰고 다음 반복으로 진행한다.
            continue

        filters_by_size[size] = pair
        print(f"✓ size_{size:<2} 필터 로드 완료 (Cross, X)")

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return filters_by_size, errors


# [함수 해설] JSON patterns 딕셔너리를 (케이스ID, 데이터) 목록으로 변환한다.
def iter_patterns(patterns_root):
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(patterns_root, dict):
        # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
        return []

    # return은 결과를 호출 위치로 돌려주고 함수를 끝낸다.
    return list(patterns_root.items())


# [함수 해설] 패턴 하나의 크기·정답을 검증하고 MAC 점수와 PASS/FAIL 이유를 딕셔너리로 반환한다.
def analyze_case(case_id, case_data, filters_by_size):
    size = extract_size_from_key(case_id)

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if size is None:
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": "케이스 키에서 크기 N을 추출할 수 없음",
        }

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if size not in filters_by_size:
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": f"size_{size}에 대응하는 정상 필터가 없음",
        }

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(case_data, dict):
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": "패턴 데이터가 객체(dict)가 아님",
        }

    pattern = case_data.get("input")
    expected_raw = case_data.get("expected")

    valid, reason = validate_matrix(pattern, size)
    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not valid:
        return {
            "id": case_id,
            "status": "FAIL",
            "reason": f"패턴 크기/스키마 오류: {reason}",
        }

    # expected 라벨도 Cross/X 표준으로 변환해 비교한다.
    expected = normalize_label(expected_raw)
    # if 조건이 참일 때만 아래 코드를 수행한다.
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

    # ==는 두 값이 같은지 판별한다. 같으면 True(통과)이다.
    passed = decision == expected

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if passed:
        reason = ""
    # 앞 조건이 거짓일 때 다른 조건을 검사한다.
    elif decision == "UNDECIDED":
        reason = (
            f"동점 규칙: |Cross-X| < {EPSILON:g} 이므로 "
            f"UNDECIDED, expected={expected}"
        )
    # 앞 조건이 모두 거짓일 때 실행한다.
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


# [함수 해설] 메뉴 2: 파일 읽기, 필터 검증, 패턴별 판정, 성능 측정, 요약 출력.
def run_json_mode():
    # Path 객체를 이용해 분석할 JSON 파일 경로를 나타낸다.
    path = Path(DATA_FILE)

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not path.exists():
        print(f"\n오류: 현재 폴더에서 {DATA_FILE}을 찾을 수 없습니다.")
        print(f"확인 위치: {path.resolve()}")
        return

    # 오류가 발생할 수 있는 동작을 시도한다.
    try:
        # with를 사용하면 파일 사용 후 자동으로 닫힌다.
        with path.open("r", encoding="utf-8") as file:
            # JSON 파일을 Python 딕셔너리·리스트 등으로 읽어 온다.
            data = json.load(file)
    # 발생한 오류를 잡아 사용자에게 설명하고 중단을 방지한다.
    except json.JSONDecodeError as exc:
        print(f"\nJSON 형식 오류: {exc}")
        return
    # 발생한 오류를 잡아 사용자에게 설명하고 중단을 방지한다.
    except OSError as exc:
        print(f"\n파일 읽기 오류: {exc}")
        return

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not isinstance(data, dict):
        print("\n오류: data.json 최상위 구조는 객체(dict)여야 합니다.")
        return

    print_title("[1] 필터 로드")

    # 오류가 발생할 수 있는 동작을 시도한다.
    try:
        filters_by_size, filter_errors = load_filters(data)
    # 발생한 오류를 잡아 사용자에게 설명하고 중단을 방지한다.
    except ValueError as exc:
        print(f"필터 스키마 오류: {exc}")
        return

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for error in filter_errors:
        print(f"✗ {error}")

    patterns_root = data.get("patterns")
    pattern_items = iter_patterns(patterns_root)

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if not pattern_items:
        print("\n오류: 분석할 patterns 항목이 없습니다.")
        return

    print_title("[2] 패턴 분석 (라벨 정규화 적용)")

    results = []

    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for case_id, case_data in pattern_items:
        result = analyze_case(case_id, case_data, filters_by_size)
        results.append(result)

        print(f"\n--- {case_id} ---")

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if "cross_score" in result:
            print(f"Cross 점수: {result['cross_score']}")
            print(f"X 점수: {result['x_score']}")
            print(
                f"판정: {result['decision']} | "
                f"expected: {result['expected']} | "
                f"{result['status']}"
            )
            # if 조건이 참일 때만 아래 코드를 수행한다.
            if result["reason"]:
                print(f"사유: {result['reason']}")
        # 앞 조건이 모두 거짓일 때 실행한다.
        else:
            print(f"판정 불가 | {result['status']}")
            print(f"사유: {result['reason']}")

    sizes = [3]
    # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
    for size in (5, 13, 25):
        # if 조건이 참일 때만 아래 코드를 수행한다.
        if size not in sizes:
            sizes.append(size)

    print_performance_table(sizes, filters_by_size)

    print_title("[4] 결과 요약")

    total = len(results)
    # 조건을 충족하는 결과마다 1을 더해 통과 수를 센다.
    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = total - passed

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    # if 조건이 참일 때만 아래 코드를 수행한다.
    if failed:
        print("\n실패 케이스:")
        # for 반복문: 각 항목에 대해 아래 들여쓴 작업을 반복한다.
        for result in results:
            # if 조건이 참일 때만 아래 코드를 수행한다.
            if result["status"] == "FAIL":
                print(f"- {result['id']}: {result['reason']}")
    # 앞 조건이 모두 거짓일 때 실행한다.
    else:
        print("\n실패 케이스 없음")
        print("라벨 정규화와 epsilon 기반 점수 비교 정책이 정상 적용되었습니다.")


# [함수 해설] 프로그램 메뉴를 무한 반복 표시하며 선택한 모드를 호출하고 0에서 종료한다.
def main():
    # 조건이 유지되는 동안 계속 반복하며 break 또는 return으로 빠져나온다.
    while True:
        print("\n=== Mini NPU Simulator ===")
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 패턴 자동 생성 (보너스)")
        print("4. 1차원 최적화 비교 (보너스)")
        print("0. 종료")

        # 메뉴 입력 문자열을 받고 양쪽 공백을 제거한다.
        choice = input("선택: ").strip()

        # if 조건이 참일 때만 아래 코드를 수행한다.
        if choice == "1":
            run_manual_mode()
        # 앞 조건이 거짓일 때 다른 조건을 검사한다.
        elif choice == "2":
            run_json_mode()
        # 앞 조건이 거짓일 때 다른 조건을 검사한다.
        elif choice == "3":
            run_generator_mode()
        # 앞 조건이 거짓일 때 다른 조건을 검사한다.
        elif choice == "4":
            run_optimization_mode()
        # 앞 조건이 거짓일 때 다른 조건을 검사한다.
        elif choice == "0":
            print("프로그램을 종료합니다.")
            # 가장 가까운 반복문을 종료한다.
            break
        # 앞 조건이 모두 거짓일 때 실행한다.
        else:
            print("입력 오류: 0, 1, 2, 3, 4 중 하나를 입력하세요.")


if __name__ == "__main__":
    main()
