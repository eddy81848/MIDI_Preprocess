import os
from collections import Counter, defaultdict

import mido

DRUMS_PROGRAM_ID = 128  # pseudo program id to represent GM channel 10 drums


def _messages_with_absolute_time(track):
    """
    Return list of message copies whose .time is converted to absolute ticks (from start of track).
    """
    abs_msgs = []
    t = 0
    for msg in track:
        t += msg.time
        abs_msgs.append(msg.copy(time=t))
    return abs_msgs


def _to_delta_time(msgs):
    """Given messages whose .time is absolute, convert in-place to delta time ordering."""
    last = 0
    for msg in msgs:
        delta = msg.time - last
        if delta < 0:
            delta = 0
        msg.time = delta
        last = last + msg.time
    return msgs


def _build_meta_track(mid_original):
    """
    Build a dedicated meta track (track 0) by copying meta messages from the original track 0
    and preserving their timing (converted back to delta). If there is no track 0, return an
    empty meta track with just end_of_track.
    """
    meta_track = mido.MidiTrack()

    if len(mid_original.tracks) > 0:
        abs_msgs = _messages_with_absolute_time(mid_original.tracks)
        meta_abs = [m.copy() for m in abs_msgs if getattr(m, "is_meta", False)]
        if meta_abs:
            # Convert back to delta and append
            _to_delta_time(meta_abs)
            meta_track.extend(meta_abs)

    # Ensure end_of_track exists
    if not (
        len(meta_track) and getattr(meta_track[-1], "type", None) == "end_of_track"
    ):
        meta_track.append(mido.MetaMessage("end_of_track", time=0))

    return meta_track


def preprocess_and_log_midi(input_dir, output_dir, log_file):
    """
    MIDI 파일을 전처리하고 통계 정보를 로그 파일로 생성합니다.

    - 한 트랙에 여러 악기가 있으면 (채널별 Program 기준) 트랙 분리
    - 드럼 채널(채널 10, 0-index로 9)은 Program Change 없이도 하나의 악기로 취급
    - 최종(메타 트랙 제외) 트랙 수가 1개 이하면 파일 스킵
    - 처리된 파일 기준, 악기 번호별(드럼은 128) 최대 트랙 수 로깅
    """
    # 로그 데이터 저장을 위한 딕셔너리
    # Key: 프로그램 번호 (0~127, 드럼=128), Value: 최대 등장 트랙 수
    max_program_counts = {}

    print("=" * 50)
    print("MIDI 전처리 및 로깅 시작...")
    print(f"입력 폴더: {input_dir}")
    print(f"출력 폴더: {output_dir}")
    print("=" * 50)

    for dirpath, _, filenames in os.walk(input_dir):
        for filename in filenames:
            if not filename.lower().endswith((".mid", ".midi")):
                continue

            input_path = os.path.join(dirpath, filename)
            print(f"\n[파일 처리 중] {input_path}")

            try:
                mid_original = mido.MidiFile(input_path)
                mid_processed = mido.MidiFile(type=1)
                mid_processed.ticks_per_beat = mid_original.ticks_per_beat

                # 1) 메타 트랙 구성 (원본 트랙 0의 메타 이벤트 복사)
                meta_track = _build_meta_track(mid_original)
                mid_processed.tracks.append(meta_track)

                # 2) 채널별 활성 Program을 추적하면서 (프로그램, 채널) 단위로 메시지 수집
                per_key_abs_msgs = defaultdict(
                    list
                )  # key=(program_id, channel) -> list of msg copies with absolute time

                for ti, track in enumerate(mid_original.tracks):
                    # 절대 시간으로 변환
                    abs_msgs = _messages_with_absolute_time(track)

                    # 채널별 활성 Program 초기값 0, 드럼 채널은 DRUMS_PROGRAM_ID로 보고
                    active_program = {ch: 0 for ch in range(16)}

                    for msg in abs_msgs:
                        # 메타 메시지는 전용 메타 트랙에서 처리하므로 건너뜀
                        if getattr(msg, "is_meta", False):
                            continue

                        # 채널이 있는 메시지들만 분배
                        ch = getattr(msg, "channel", None)
                        if ch is None:
                            continue

                        if msg.type == "program_change":
                            active_program[ch] = msg.program
                            # program_change 자체도 해당 키로 라우팅 (선택사항)
                        # 드럼 채널은 항상 DRUMS_PROGRAM_ID로 묶기
                        program_id = DRUMS_PROGRAM_ID if ch == 9 else active_program[ch]

                        # 복사하여 절대시간 유지
                        per_key_abs_msgs[(program_id, ch)].append(msg.copy())

                # 3) 수집된 각 (program, channel) 묶음으로 트랙 생성 (절대->델타 변환)
                instrument_tracks_info = []  # list of (program_id, track)

                for (program_id, ch), msgs in per_key_abs_msgs.items():
                    # 시간 순으로 정렬 (혹시 섞여 있다면)
                    msgs.sort(key=lambda m: m.time)

                    # 절대 -> 델타 변환
                    _to_delta_time(msgs)

                    new_track = mido.MidiTrack()
                    name = f'Ch {ch} - Prog {program_id if program_id != DRUMS_PROGRAM_ID else "Drums"}'
                    new_track.append(mido.MetaMessage("track_name", name=name, time=0))
                    new_track.extend(msgs)
                    new_track.append(mido.MetaMessage("end_of_track", time=0))

                    # 유효 노트가 있는지 확인
                    has_notes = any(
                        (m.type == "note_on" and m.velocity > 0) or m.type == "note_off"
                        for m in msgs
                    )
                    if has_notes:
                        mid_processed.tracks.append(new_track)
                        instrument_tracks_info.append((program_id, new_track))

                final_track_count = len(instrument_tracks_info)
                if final_track_count <= 1:
                    print(
                        f"  - 스킵: 최종 트랙 수가 {final_track_count}개이므로 저장하지 않습니다."
                    )
                    continue

                print(
                    f"  - 유효: 최종 트랙 수 {final_track_count}개. 저장을 진행합니다."
                )

                # 4) 파일별 Program별 트랙 수 집계 (메타 트랙 제외)
                counts_in_file = Counter([prog for (prog, _) in instrument_tracks_info])
                for program_num, count in counts_in_file.items():
                    if count > max_program_counts.get(program_num, 0):
                        max_program_counts[program_num] = count
                        print(
                            f"  - 로그 갱신: 악기 {program_num}의 최대 트랙 수 -> {count}개"
                        )

                # 5) 저장 (원본 디렉토리 구조 유지)
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
    INPUT_DIRECTORY = "midi_input"
    OUTPUT_DIRECTORY = "midi_output"
    LOG_FILENAME = "log_data.txt"

    if not os.path.isdir(INPUT_DIRECTORY):
        os.makedirs(INPUT_DIRECTORY)
        print(
            f"'{INPUT_DIRECTORY}' 폴더가 생성되었습니다. 이 곳에 MIDI 파일들을 넣어주세요."
        )
    else:
        preprocess_and_log_midi(INPUT_DIRECTORY, OUTPUT_DIRECTORY, LOG_FILENAME)
