import os

import mido


def extract_instrument_names(midi_directory, output_file):
    """
    지정된 디렉토리의 모든 MIDI 파일에서 트랙 이름을 추출하여 텍스트 파일로 저장합니다.

    :param midi_directory: MIDI 파일들이 있는 디렉토리 경로
    :param output_file: 추출된 트랙 이름을 저장할 파일 경로
    """
    instrument_names = set()  # 중복된 이름을 자동으로 제거하기 위해 set을 사용합니다.

    print(f"'{midi_directory}' 폴더에서 MIDI 파일을 검색합니다...")

    # 디렉토리의 모든 파일을 확인합니다.
    for filename in os.listdir(midi_directory):
        # 파일 확장자가 .mid 또는 .midi 인 경우에만 처리합니다.
        if filename.lower().endswith((".mid", ".midi")):
            file_path = os.path.join(midi_directory, filename)
            try:
                mid = mido.MidiFile(file_path)
                # MIDI 파일의 각 트랙을 순회합니다.
                for i, track in enumerate(mid.tracks):
                    # 트랙의 각 메시지를 확인합니다.
                    for msg in track:
                        # 메시지 타입이 'track_name'인 경우 이름을 추출합니다.
                        if msg.type == "track_name":
                            # 공백 제거 후 이름 추가
                            instrument_names.add(msg.name.strip())
            except Exception as e:
                print(f"'{filename}' 파일을 처리하는 중 오류 발생: {e}")

    # 추출된 이름들을 알파벳 순서로 정렬합니다.
    sorted_names = sorted(list(instrument_names))

    # 결과를 파일에 저장합니다.
    with open(output_file, "w", encoding="utf-8") as f:
        for name in sorted_names:
            f.write(name + "\n")

    print(
        f"\n총 {len(sorted_names)}개의 고유한 악기 이름을 찾아 '{output_file}'에 저장했습니다."
    )
    print("이제 이 파일을 열어 악기 이름을 어떻게 분류할지 확인해 보세요!")


if __name__ == "__main__":
    # MIDI 파일이 저장된 폴더 경로를 지정해주세요.
    MIDI_INPUT_DIR = "midi_files"
    # 추출된 악기 이름 목록을 저장할 파일 이름을 지정해주세요.
    OUTPUT_TXT_FILE = "instrument_list.txt"

    # MIDI 입력 폴더가 없으면 생성합니다.
    if not os.path.exists(MIDI_INPUT_DIR):
        os.makedirs(MIDI_INPUT_DIR)
        print(
            f"'{MIDI_INPUT_DIR}' 폴더가 없어 새로 만들었습니다. 이 폴더에 MIDI 파일들을 넣어주세요."
        )
    else:
        extract_instrument_names(MIDI_INPUT_DIR, OUTPUT_TXT_FILE)
