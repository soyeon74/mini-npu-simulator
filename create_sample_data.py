"""학습용 예제 data.json 생성기. 공식 과제 데이터가 아닙니다."""

import json
from pathlib import Path

from main import generate_cross, generate_x


# [함수 해설] 네 가지 크기에 대한 Cross/X 예제 필터와 정답 패턴을 딕셔너리로 만든다.
def build_sample_data():
    # JSON 최상위 키: 공식 데이터가 아니라는 안내, 필터, 패턴.
    data = {
        "_notice": "학습 및 검증용 예제. 교육기관의 공식 과제 data.json이 아닙니다.",
        "filters": {},
        "patterns": {},
    }

    # size를 3, 5, 13, 25로 바꿔가며 같은 생성 과정을 반복한다.
    for size in (3, 5, 13, 25):
        # 해당 크기의 십자가 배열을 만든다.
        cross = generate_cross(size)
        # 해당 크기의 X 배열을 만든다.
        x_pattern = generate_x(size)
        # 두 필터를 size_N이라는 이름 아래 저장한다.
        data["filters"][f"size_{size}"] = {"cross": cross, "x": x_pattern}
        # 첫 예제는 십자가이며 expected는 +로 저장한다.
        data["patterns"][f"size_{size}_1"] = {"input": cross, "expected": "+"}
        # 두 번째 예제는 X이며 expected는 x로 저장한다.
        data["patterns"][f"size_{size}_2"] = {"input": x_pattern, "expected": "x"}

    # 파일에 저장할 JSON의 원본이 되는 딕셔너리 반환.
    return data


# 이 파일을 직접 실행할 때만 아래 생성·저장 코드를 실행한다.
if __name__ == "__main__":
    # 현재 코드 파일과 같은 폴더의 data.json을 저장 대상 파일로 정한다.
    output = Path(__file__).with_name("data.json")
    # 이미 파일이 있다면 사용자의 yes 입력 없이는 덮어쓰지 않는다.
    if output.exists():
        answer = input("기존 data.json을 예제 데이터로 덮어쓸까요? (yes 입력): ").strip()
        if answer != "yes":
            print("파일을 변경하지 않았습니다.")
            raise SystemExit(0)
    # 딕셔너리를 들여쓰기된 UTF-8 JSON 텍스트로 저장한다.
    output.write_text(json.dumps(build_sample_data(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"학습용 예제 생성 완료: {output}")
