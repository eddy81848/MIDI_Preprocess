import json
import os

import mido

# --- 설정 ---
# MIDI 파일이 있는 입력 폴더
INPUT_DIR = "midi_output"
# 변경된 MIDI 파일이 저장될 출력 폴더
OUTPUT_DIR = "midi_final"
# 악기 번호 변경 규칙이 담긴 JSON 파일
MAP_FILE = "program_map.json"


def load_program_map(file_path):
    """JSON 맵 파일을 안전하게 불러옵니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"오류: 맵 파일 '{file_path}'를 찾을 수 없습니다. 스크립트를 종료합니다.")
        return None
    except json.JSONDecodeError:
        print(
            f"오류: 맵 파일 '{file_path}'의 JSON 형식이 잘못되었습니다. 스크립트를 종료합니다."
        )
        return None


def apply_program_map(input_dir, output_dir, program_map):
    """
    MIDI 파일들의 Program Change를 맵에 따라 변경하고 새 폴더에 저장합니다.
    """
    print("=" * 50)
    print(f"'{input_dir}' 폴더의 MIDI 파일 처리를 시작합니다.")

    # 입력 디렉토리의 모든 파일과 하위 폴더를 순회
    for dirpath, _, filenames in os.walk(input_dir):
        for filename in filenames:
            # MIDI 파일이 아니면 건너뛰기
            if not filename.lower().endswith((".mid", ".midi")):
                continue

            input_path = os.path.join(dirpath, filename)

            try:
                mid = mido.MidiFile(input_path)
                changes_count = 0

                # 각 트랙의 메시지를 확인하며 Program Change 변경
                for track in mid.tracks:
                    for msg in track:
                        if msg.type == "program_change":
                            # JSON의 키는 문자열이므로, 프로그램 번호를 문자열로 변환하여 확인
                            program_str = str(msg.program)
                            if program_str in program_map:
                                new_program_num = program_map[program_str]
                                if msg.program != new_program_num:
                                    msg.program = new_program_num
                                    changes_count += 1

                # 원본 디렉토리 구조를 유지하여 출력 경로 설정
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, relative_path)

                # 출력 폴더가 없으면 생성
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # 변경된 MIDI 파일 저장
                mid.save(output_path)

                if changes_count > 0:
                    print(
                        f"  - '{filename}': {changes_count}개 악기 변경 후 저장 완료."
                    )
                else:
                    print(f"  - '{filename}': 변경 사항 없음. 그대로 복사 완료.")

            except Exception as e:
                print(f"  - 오류: '{filename}' 처리 중 문제 발생 - {e}")

    print("=" * 50)
    print("✅ 모든 작업이 완료되었습니다.")
    print(f"최종 결과물은 '{output_dir}' 폴더를 확인해주세요.")


# --- 메인 실행 부분 ---
if __name__ == "__main__":
    # 1. 맵 파일 로드
    program_map = load_program_map(MAP_FILE)

    # 2. 맵과 입력 폴더가 정상적일 때만 메인 로직 실행
    if program_map and os.path.isdir(INPUT_DIR):
        apply_program_map(INPUT_DIR, OUTPUT_DIR, program_map)
    elif not os.path.isdir(INPUT_DIR):
        print(
            f"오류: 입력 폴더 '{INPUT_DIR}'를 찾을 수 없습니다. 폴더를 생성하고 MIDI 파일을 넣어주세요."
        )
