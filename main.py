import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

EPSILON = 1e-9
REPEATS = 10

STANDARD_CROSS = "Cross"
STANDARD_X = "X"
STANDARD_UNDECIDED = "UNDECIDED"


Matrix = List[List[float]]


def load_dotenv_if_exists(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    try:
        with path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError as exc:
        print(f".env 로드 중 오류 발생: {exc}")


def normalize_label(value: str) -> Optional[str]:
    lowered = str(value).strip().lower()
    if lowered in {"+", "cross"}:
        return STANDARD_CROSS
    if lowered in {"x"}:
        return STANDARD_X
    return None


def normalize_filter_map(raw_filter_map: Dict[str, Matrix]) -> Tuple[Optional[Dict[str, Matrix]], Optional[str]]:
    normalized: Dict[str, Matrix] = {}
    for key, matrix in raw_filter_map.items():
        normalized_label = normalize_label(key)
        if normalized_label is None:
            return None, f"지원하지 않는 필터 라벨: {key}"
        normalized[normalized_label] = matrix

    if STANDARD_CROSS not in normalized or STANDARD_X not in normalized:
        return None, "필터는 Cross/cross/+ 와 X/x 라벨을 모두 포함해야 합니다."

    return normalized, None


def validate_matrix(matrix: Matrix, size: int) -> Tuple[bool, Optional[str]]:
    if not isinstance(matrix, list) or len(matrix) != size:
        return False, f"행 수 불일치: 기대 {size}, 실제 {len(matrix) if isinstance(matrix, list) else 'N/A'}"

    for row in matrix:
        if not isinstance(row, list) or len(row) != size:
            return False, f"열 수 불일치: 각 행은 {size}개의 값이어야 합니다."
        for v in row:
            if not isinstance(v, (int, float)):
                return False, f"숫자 파싱 실패: {v}"

    return True, None


def read_matrix_from_console(size: int, title: str) -> Matrix:
    print(title)
    while True:
        rows: Matrix = []
        ok = True
        for _ in range(size):
            line = input().strip()
            parts = line.split()
            if len(parts) != size:
                ok = False
                break
            try:
                rows.append([float(x) for x in parts])
            except ValueError:
                ok = False
                break

        if ok:
            return rows

        print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
        print(title)


def mac_score(input_matrix: Matrix, filter_matrix: Matrix) -> float:
    size = len(input_matrix)
    total = 0.0
    for i in range(size):
        for j in range(size):
            total += input_matrix[i][j] * filter_matrix[i][j]
    return total


def decide_label(score_cross: float, score_x: float, epsilon: float = EPSILON) -> str:
    if abs(score_cross - score_x) < epsilon:
        return STANDARD_UNDECIDED
    if score_cross > score_x:
        return STANDARD_CROSS
    return STANDARD_X


def average_mac_time_ms(input_matrix: Matrix, filter_matrix: Matrix, repeats: int = REPEATS) -> float:
    start = time.perf_counter()
    for _ in range(repeats):
        mac_score(input_matrix, filter_matrix)
    end = time.perf_counter()
    return ((end - start) * 1000.0) / repeats


def print_mode1_multiplication_preview(pattern: Matrix, filter_a: Matrix, filter_b: Matrix) -> None:
    print("\n[곱셈 미리보기]")
    print("같은 칸끼리 곱해서 더해요.")
    print("예시(첫 줄):")

    a_row = " + ".join(
        f"({int(pattern[0][j]) if pattern[0][j].is_integer() else pattern[0][j]}x"
        f"{int(filter_a[0][j]) if filter_a[0][j].is_integer() else filter_a[0][j]})"
        for j in range(3)
    )
    b_row = " + ".join(
        f"({int(pattern[0][j]) if pattern[0][j].is_integer() else pattern[0][j]}x"
        f"{int(filter_b[0][j]) if filter_b[0][j].is_integer() else filter_b[0][j]})"
        for j in range(3)
    )

    print(f"A 첫 줄: {a_row}")
    print(f"B 첫 줄: {b_row}")


def generate_cross_pattern(size: int) -> Matrix:
    center = size // 2
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    for i in range(size):
        matrix[i][center] = 1.0
        matrix[center][i] = 1.0
    return matrix


def generate_x_pattern(size: int) -> Matrix:
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    for i in range(size):
        matrix[i][i] = 1.0
        matrix[i][size - 1 - i] = 1.0
    return matrix


def mode_user_input() -> None:
    print("\n#----------------------------------------")
    print("# 1단계: 기준 그림(필터) 2개 넣기")
    print("#----------------------------------------")
    filter_a = read_matrix_from_console(3, "필터 A (3줄 입력, 공백 구분)")
    filter_b = read_matrix_from_console(3, "필터 B (3줄 입력, 공백 구분)")
    print("저장 완료: A, B 필터를 기억했어요.")

    print("\n#----------------------------------------")
    print("# 2단계: 맞춰볼 그림(패턴) 넣기")
    print("#----------------------------------------")
    pattern = read_matrix_from_console(3, "패턴 (3줄 입력, 공백 구분)")

    print_mode1_multiplication_preview(pattern, filter_a, filter_b)

    score_a = mac_score(pattern, filter_a)
    score_b = mac_score(pattern, filter_b)

    if abs(score_a - score_b) < EPSILON:
        decision = "판정 불가"
    elif score_a > score_b:
        decision = "A"
    else:
        decision = "B"

    perf_ms = average_mac_time_ms(pattern, filter_a, REPEATS)

    print("\n#----------------------------------------")
    print("# 3단계: 점수 비교 결과")
    print("#----------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEATS}회): {perf_ms:.6f} ms")
    if decision == "판정 불가":
        print(f"판정: 판정 불가 (두 점수 차이가 아주 작아요: |A-B| < {EPSILON})")
    else:
        print(f"판정: {decision}가 더 닮았어요!")


def load_json_data(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def analyze_json_mode(data_path: Path) -> None:
    print("\n#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")

    if not data_path.exists():
        print(f"data.json 파일을 찾을 수 없습니다: {data_path}")
        return

    try:
        data = load_json_data(data_path)
    except Exception as exc:
        print(f"data.json 로드 실패: {exc}")
        return

    filters = data.get("filters", {})
    patterns = data.get("patterns", {})

    normalized_filters_by_size: Dict[int, Dict[str, Matrix]] = {}

    for size in [5, 13, 25]:
        key = f"size_{size}"
        raw_filter_map = filters.get(key)
        if not isinstance(raw_filter_map, dict):
            print(f"✗ {key} 필터 누락 또는 형식 오류")
            continue

        normalized_filter_map, err = normalize_filter_map(raw_filter_map)
        if err:
            print(f"✗ {key} 필터 로드 실패: {err}")
            continue

        cross_ok, cross_err = validate_matrix(normalized_filter_map[STANDARD_CROSS], size)
        x_ok, x_err = validate_matrix(normalized_filter_map[STANDARD_X], size)
        if not cross_ok:
            print(f"✗ {key} Cross 검증 실패: {cross_err}")
            continue
        if not x_ok:
            print(f"✗ {key} X 검증 실패: {x_err}")
            continue

        normalized_filters_by_size[size] = normalized_filter_map
        print(f"✓ {key} 필터 로드 완료 (Cross, X)")

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")

    total = 0
    passed = 0
    failed: List[Tuple[str, str]] = []

    for case_id, item in patterns.items():
        total += 1
        print(f"--- {case_id} ---")

        if not isinstance(item, dict):
            reason = "패턴 항목 형식 오류"
            print(f"FAIL ({reason})")
            failed.append((case_id, reason))
            continue

        m = re.match(r"^size_(\d+)_\d+$", case_id)
        if not m:
            reason = "케이스 키 규칙 불일치(size_{N}_{idx})"
            print(f"FAIL ({reason})")
            failed.append((case_id, reason))
            continue

        size = int(m.group(1))
        if size not in normalized_filters_by_size:
            reason = f"size_{size} 필터를 찾을 수 없음"
            print(f"FAIL ({reason})")
            failed.append((case_id, reason))
            continue

        input_matrix = item.get("input")
        expected_raw = item.get("expected")

        input_ok, input_err = validate_matrix(input_matrix, size)
        if not input_ok:
            reason = f"입력 매트릭스 검증 실패: {input_err}"
            print(f"FAIL ({reason})")
            failed.append((case_id, reason))
            continue

        expected_normalized = normalize_label(str(expected_raw))
        if expected_normalized is None:
            reason = f"expected 라벨 정규화 실패: {expected_raw}"
            print(f"FAIL ({reason})")
            failed.append((case_id, reason))
            continue

        selected_filters = normalized_filters_by_size[size]
        score_cross = mac_score(input_matrix, selected_filters[STANDARD_CROSS])
        score_x = mac_score(input_matrix, selected_filters[STANDARD_X])

        predicted = decide_label(score_cross, score_x, EPSILON)
        is_pass = predicted == expected_normalized

        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")
        print(
            f"판정: {predicted} | expected: {expected_normalized} | {'PASS' if is_pass else 'FAIL'}"
        )

        if is_pass:
            passed += 1
        else:
            reason = "예상 라벨과 판정 불일치(동점 규칙 포함)"
            failed.append((case_id, reason))

    print("\n#----------------------------------------")
    print(f"# [3] 성능 분석 (평균/{REPEATS}회)")
    print("#----------------------------------------")
    print(f"{'크기':<10}{'평균 시간(ms)':<18}{'연산 횟수(N^2)'}")
    print("-" * 45)

    for size in [3, 5, 13, 25]:
        if size == 3:
            test_input = generate_cross_pattern(3)
            test_filter = generate_cross_pattern(3)
            avg_ms = average_mac_time_ms(test_input, test_filter, REPEATS)
            print(f"{size}x{size:<7}{avg_ms:<18.6f}{size * size}")
            continue

        if size in normalized_filters_by_size:
            test_input = normalized_filters_by_size[size][STANDARD_CROSS]
            test_filter = normalized_filters_by_size[size][STANDARD_CROSS]
            avg_ms = average_mac_time_ms(test_input, test_filter, REPEATS)
            print(f"{size}x{size:<7}{avg_ms:<18.6f}{size * size}")
        else:
            print(f"{size}x{size:<7}{'N/A':<18}{size * size}")

    print("\n#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {total - passed}개")

    if failed:
        print("\n실패 케이스:")
        for case_id, reason in failed:
            print(f"- {case_id}: {reason}")


def main() -> None:
    load_dotenv_if_exists(Path(".env"))

    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]\n")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        mode = input("선택: ").strip()
        if mode in {"1", "2"}:
            break
        print("입력 오류: 1 또는 2를 입력하세요.")

    if mode == "1":
        mode_user_input()
    else:
        analyze_json_mode(Path("data.json"))


if __name__ == "__main__":
    main()
