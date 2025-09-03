import json
import os

import mido


def modify_instrument_names(midi_directory, output_directory, mapping_file):
    """
    매핑 파일에 정의된 규칙에 따라 MIDI 파일의 트랙 이름을 변경하고
    새 디렉토리에 저장합니다.

    :param midi_directory: 원본 MIDI 파일들이 있는 디렉토리
    :param output_directory: 수정된 MIDI 파일을 저장할 디렉토리
    :param mapping_file: 악기 이름 매핑 규칙이 담긴 JSON 파일
    """
    # 매핑 파일을 읽어옵니다.
    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            name_map = json.load(f)
    except FileNotFoundError:
        print(f"오류: 매핑 파일 '{mapping_file}'을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print(f"오류: '{mapping_file}'이 올바른 JSON 형식이 아닙니다.")
        return

    # 결과를 저장할 폴더가 없으면 새로 만듭니다.
    os.makedirs(output_directory, exist_ok=True)

    print(
        f"'{midi_directory}' 폴더의 MIDI 파일들을 변환하여 '{output_directory}'에 저장합니다."
    )

    # 디렉토리의 모든 파일을 확인합니다.
    for filename in os.listdir(midi_directory):
        if filename.lower().endswith((".mid", ".midi")):
            input_path = os.path.join(midi_directory, filename)
            output_path = os.path.join(output_directory, filename)

            try:
                mid = mido.MidiFile(input_path)
                changes_made = False
                # MIDI 파일의 각 트랙을 순회합니다.
                for track in mid.tracks:
                    # 트랙의 각 메시지를 확인합니다.
                    for msg in track:
                        if msg.type == "track_name":
                            original_name = msg.name.strip()
                            # 현재 이름이 매핑 파일에 정의되어 있는지 확인합니다.
                            if original_name in name_map:
                                new_name = name_map[original_name]
                                # 이름이 실제로 바뀔 경우에만 로그를 남깁니다.
                                if original_name != new_name:
                                    print(
                                        f"  - 파일 '{filename}': '{original_name}' -> '{new_name}'"
                                    )
                                    msg.name = new_name
                                    changes_made = True

                # 변경된 MIDI 파일을 저장합니다.
                mid.save(output_path)

            except Exception as e:
                print(f"'{filename}' 파일을 처리하는 중 오류 발생: {e}")

    print("\n모든 작업이 완료되었습니다!")


if __name__ == "__main__":
    # 원본 MIDI 파일이 저장된 폴더
    MIDI_INPUT_DIR = "midi_files"
    # 이름이 수정된 MIDI 파일을 저장할 폴더
    MIDI_OUTPUT_DIR = "midi_files_modified"
    # 직접 작성한 악기 이름 분류 기준 파일
    MAPPING_FILE = "instrument_map.json"

    modify_instrument_names(MIDI_INPUT_DIR, MIDI_OUTPUT_DIR, MAPPING_FILE)
