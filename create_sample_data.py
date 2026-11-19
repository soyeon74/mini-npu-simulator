"""학습용 예제 data.json 생성기. 공식 과제 데이터가 아닙니다."""

import json
from pathlib import Path

from main import generate_cross, generate_x


def build_sample_data():
    data = {
        "_notice": "학습 및 검증용 예제. 교육기관의 공식 과제 data.json이 아닙니다.",
        "filters": {},
        "patterns": {},
    }

    for size in (3, 5, 13, 25):
        cross = generate_cross(size)
        x_pattern = generate_x(size)
        data["filters"][f"size_{size}"] = {"cross": cross, "x": x_pattern}
        data["patterns"][f"size_{size}_1"] = {"input": cross, "expected": "+"}
        data["patterns"][f"size_{size}_2"] = {"input": x_pattern, "expected": "x"}

    return data


if __name__ == "__main__":
    output = Path(__file__).with_name("data.json")
    if output.exists():
        answer = input("기존 data.json을 예제 데이터로 덮어쓸까요? (yes 입력): ").strip()
        if answer != "yes":
            print("파일을 변경하지 않았습니다.")
            raise SystemExit(0)
    output.write_text(json.dumps(build_sample_data(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"학습용 예제 생성 완료: {output}")
