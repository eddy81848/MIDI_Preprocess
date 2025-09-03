import mido


def get_track_info(midi_filepath):
    """
    MIDI 파일의 각 트랙별 이름, 프로그램 번호, 채널 정보를 추출하여 출력합니다.

    :param midi_filepath: 분석할 MIDI 파일의 경로
    """
    try:
        mid = mido.MidiFile(midi_filepath)
    except Exception as e:
        print(f"'{midi_filepath}' 파일을 여는 데 실패했습니다: {e}")
        return

    print(f"🎵 파일 분석: {midi_filepath}\n")

    # 각 트랙을 순회하며 정보를 추출합니다.
    # enumerate를 사용해 트랙 번호(i)를 함께 가져옵니다.
    for i, track in enumerate(mid.tracks):
        track_name = "이름 없음"  # 기본값 설정
        program_number = "지정 안됨"  # 기본값 설정
        channel_number = "N/A"  # 기본값 설정
        tmp: int = None

        # 트랙의 모든 메시지를 확인합니다.
        for msg in track:
            # 메시지 타입이 'track_name'인 경우
            if msg.type == "track_name":
                track_name = msg.name.strip()

            # 메시지 타입이 'program_change'인 경우
            # 한 트랙에 여러 program_change가 있을 수 있으므로, 보통 가장 먼저 나오는 것을 사용합니다.
            if msg.type == "program_change":
                # 아직 program_number가 기본값일 때만 값을 할당합니다.
                if program_number == "지정 안됨":
                    program_number = msg.program
                    channel_number = msg.channel
                    tmp = int(program_number) + 1

        # 최종 추출된 정보를 출력합니다.
        print(f"=============== 트랙 {i} ===============")
        print(f"  - 트랙 이름: {track_name}")
        print(f"  - 채널 번호: {channel_number}")
        print(f"  - 악기 번호 (Program Change): {tmp}")
        print("=" * 35 + "\n")


if __name__ == "__main__":
    # 여기에 분석하고 싶은 미디 파일의 이름을 입력하세요.
    # 스크립트와 같은 폴더에 파일을 두면 편리합니다.
    MIDI_FILE = "midi/Highway_To_Hell.1.mid"

    get_track_info(MIDI_FILE)
