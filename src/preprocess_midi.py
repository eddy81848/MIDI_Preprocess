import os
from collections import Counter

import mido


def preprocess_and_log_midi(input_dir, output_dir, log_file):
    """
    MIDI 파일을 전처리하고 통계 정보를 로그 파일로 생성합니다.

    - 한 트랙에 여러 악기가 있으면 트랙 분리
    - 최종 트랙 수가 1개 이하면 파일 스킵
    - 처리된 파일 기준, 악기 번호별 최대 트랙 수 로깅
    """
    # 로그 데이터 저장을 위한 딕셔너리
    # Key: 프로그램 번호, Value: 최대 등장 횟수(트랙 수)
    max_program_counts = {}

    print("=" * 50)
    print(f"MIDI 전처리 및 로깅 시작...")
    print(f"입력 폴더: {input_dir}")
    print(f"출력 폴더: {output_dir}")
    print("=" * 50)

    # 입력 디렉토리 순회
    for dirpath, _, filenames in os.walk(input_dir):
        for filename in filenames:
            if not filename.lower().endswith((".mid", ".midi")):
                continue

            input_path = os.path.join(dirpath, filename)
            print(f"\n[파일 처리 중] {input_path}")

            try:
                # 1. 원본 MIDI 로드 및 처리 결과를 담을 새 MIDI 객체 생성
                mid_original = mido.MidiFile(input_path)
                mid_processed = mido.MidiFile(type=1)
                mid_processed.ticks_per_beat = mid_original.ticks_per_beat

                # 2. 한 트랙에 여러 Program Change가 있으면 분리
                for i, track in enumerate(mid_original.tracks):
                    program_changes = [
                        msg for msg in track if msg.type == "program_change"
                    ]

                    if len(program_changes) <= 1:
                        mid_processed.tracks.append(track)
                    else:
                        print(f"  - 트랙 {i} 분리: {len(program_changes)}개 악기 발견")
                        messages_by_program = {}
                        current_program = None
                        for msg in track:
                            if msg.type == "program_change":
                                current_program = msg.program
                                if current_program not in messages_by_program:
                                    messages_by_program[current_program] = []
                            if current_program is not None:
                                messages_by_program[current_program].append(msg)

                        for program_num, messages in messages_by_program.items():
                            new_track = mido.MidiTrack()
                            new_track.append(
                                mido.Message(
                                    "track_name",
                                    name=f"Trk {i} (Split) - Prog {program_num}",
                                )
                            )
                            new_track.extend(messages)
                            mid_processed.tracks.append(new_track)

                # 3. 최종 트랙 개수 확인
                final_track_count = len(mid_processed.tracks)

                # 4. 트랙 수가 1개 이하면 스킵
                if final_track_count <= 1:
                    print(
                        f"  - 스킵: 최종 트랙 수가 {final_track_count}개이므로 저장하지 않습니다."
                    )
                    continue

                print(
                    f"  - 유효: 최종 트랙 수 {final_track_count}개. 저장을 진행합니다."
                )

                # 5 & 6. 로그 기록 및 최댓값 갱신
                programs_in_file = [
                    msg.program
                    for track in mid_processed.tracks
                    for msg in track
                    if msg.type == "program_change"
                ]
                counts_in_file = Counter(programs_in_file)

                for program_num, count in counts_in_file.items():
                    if count > max_program_counts.get(program_num, 0):
                        max_program_counts[program_num] = count
                        print(
                            f"  - 로그 갱신: 악기 {program_num}의 최대 트랙 수 -> {count}개"
                        )

                # 처리된 파일 저장 (원본 디렉토리 구조 유지)
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, relative_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                mid_processed.save(output_path)

            except Exception as e:
                print(f"  - 오류 발생: {e}")

    # 모든 파일 처리 후 최종 로그 파일 생성
    print("\n" + "=" * 50)
    print("모든 파일 처리 완료. 최종 로그 파일을 생성합니다.")
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Program Number | Max Tracks in a Single File\n")
            f.write("-------------------------------------------\n")
            for program_num in sorted(max_program_counts.keys()):
                count = max_program_counts[program_num]
                f.write(f"{program_num:<14} | {count}\n")
        print(f"✅ 로그 파일이 '{log_file}'에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"로그 파일 저장 중 오류 발생: {e}")
    print("=" * 50)


if __name__ == "__main__":
    # 입력 폴더 (이 폴더 안에 MIDI 파일들을 넣어주세요)
    INPUT_DIRECTORY = "midi_input"
    # 전처리된 파일이 저장될 출력 폴더
    OUTPUT_DIRECTORY = "midi_output"
    # 통계 로그 파일 이름
    LOG_FILENAME = "log_data.txt"

    # 입력 폴더가 없으면 생성
    if not os.path.isdir(INPUT_DIRECTORY):
        os.makedirs(INPUT_DIRECTORY)
        print(
            f"'{INPUT_DIRECTORY}' 폴더가 생성되었습니다. 이 곳에 MIDI 파일들을 넣어주세요."
        )
    else:
        preprocess_and_log_midi(INPUT_DIRECTORY, OUTPUT_DIRECTORY, LOG_FILENAME)
