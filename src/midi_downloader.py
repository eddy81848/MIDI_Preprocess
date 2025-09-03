import os
import random
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def log_download_failure(log_file, file_info="error"):
    """실패한 다운로드 정보를 로그 파일에 기록하는 함수"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] - Failed File: {file_info}\n")


def download_midi_files_flexible(
    username, password, download_list, download_path=".", log_file="error_log.txt"
):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] - Download Start\n")
    """
    [작곡가] 또는 [작곡가, 카테고리] 형식에 따라 유연하게 MIDI 파일을 다운로드하는 함수
    """
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": os.path.abspath(download_path)}
    options.add_experimental_option("prefs", prefs)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 1. 로그인
        print("로그인 페이지로 이동 및 로그인 시도...")
        driver.get("https://www.kunstderfuge.com/-/db/log-in.asp")
        driver.find_element(By.NAME, "Email").send_keys(username)
        driver.find_element(By.NAME, "Password").send_keys(password)
        driver.find_element(By.NAME, "Submit").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Logout"))
        )
        print("로그인 성공!")
        time.sleep(random.uniform(1, 3))

        # 2. 지정된 목록 순차적으로 다운로드
        for item in download_list:
            if len(item) == 2:
                target_dir = os.path.join(download_path, item[0] + " - " + item[1])
            else:
                target_dir = os.path.join(download_path, item[0])
            os.makedirs(target_dir, exist_ok=True)

            # 다운로드 전 현재 폴더 상태 저장
            files_before = set(os.listdir(download_path))
            try:
                # 메인 MIDI 목록 페이지로 이동
                driver.get("https://www.kunstderfuge.com/midi.htm")
                time.sleep(random.uniform(1, 2))

                target_link = None

                # Case 1: [작곡가, 카테고리] 형식
                if len(item) == 2:
                    composer, category = item
                    print(f"\n--- '{composer}'의 '{category}' 작업 시작 ---")

                    # 가장 정확한 XPath 탐색 로직으로 최종 수정
                    # 1단계: 작곡가 링크를 포함하는 <b> 태그의 직속 부모 <li>를 찾아 영역으로 확정
                    print("1단계: 정확한 작곡가 영역을 찾습니다...")
                    composer_area_xpath = (
                        f"//b[a[contains(text(), '{composer}')]]/parent::li"
                    )
                    composer_area = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, composer_area_xpath))
                    )

                    # 2단계: 찾아낸 영역 안에서만 카테고리 링크 찾기
                    print("2단계: 해당 영역 안에서 카테고리 링크를 찾습니다...")
                    target_link = composer_area.find_element(By.LINK_TEXT, category)

                # Case 2: [작곡가] 형식
                elif len(item) == 1:
                    composer = item[0]
                    print(f"\n--- '{composer}' 작곡가 작업 시작 ---")
                    print(f"이름으로 메인 링크를 찾습니다...")
                    target_link = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, composer))
                    )

                else:
                    print(f"\n[오류] 잘못된 형식의 항목입니다: {item}. 건너뜁니다.")
                    continue

                print("링크를 찾았습니다. 페이지로 이동합니다.")
                target_link.click()
                time.sleep(random.uniform(2, 4))  # 페이지 로딩 대기

                download_link_elements = driver.find_elements(
                    By.XPATH, "//a[@class='white' and contains(text(), 'MIDI')]"
                )
                urls_to_download = [
                    link.get_attribute("href")
                    for link in download_link_elements
                    if link.get_attribute("href")
                ]

                # 3. 새 페이지에서 모든 MIDI 다운로드 링크 찾기 및 다운로드
                download_links = driver.find_elements(
                    By.XPATH, "//a[@class='white' and contains(text(), 'MIDI')]"
                )

                if not download_links:
                    print(f"페이지에서 MIDI 다운로드 링크를 찾을 수 없습니다.")
                    continue

                print(f"총 {len(download_links)}개의 MIDI 파일을 다운로드합니다.")
                error_file_name = "error"
                for url in urls_to_download:
                    try:
                        # current_link = driver.find_elements(
                        #     By.XPATH, "//a[@class='white' and contains(text(), 'MIDI')]"
                        # )[i]
                        # file_name = current_link.get_attribute("href").split("file=")[
                        #     -1
                        # ]
                        # error_file_name = file_name
                        # print(f"- 다운로드 중: {file_name}")
                        # current_link.click()
                        # time.sleep(random.uniform(1.5, 3.5))
                        file_name_info = url.split("file=")[-1]
                        error_file_name = file_name_info
                        print(f"- 다운로드 시도: {file_name_info}")
                        driver.get(url)  # URL로 직접 이동하여 다운로드 트리거
                        time.sleep(random.uniform(1.5, 3.5))
                    except Exception as e:
                        print(f"  [!] 개별 파일 다운로드 중 오류 발생: {e}")
                        log_download_failure(log_file, error_file_name)
                        print("  [!] 해당 파일을 건너뛰고 다음 파일로 계속 진행합니다.")
                        continue

                files_after = set(os.listdir(download_path))
                newly_downloaded = files_after - files_before
                time.sleep(5)
                for file in newly_downloaded:
                    # 임시 다운로드 파일(.crdownload)은 무시
                    if file.endswith(".crdownload"):
                        continue
                    shutil.move(os.path.join(download_path, file), target_dir)
                print(f"'{target_dir}'로 이동 완료")
            except TimeoutException:
                print(f"페이지에서 '{item}'에 해당하는 링크를 찾을 수 없습니다.")
            except Exception as e:
                print(f"'{item}' 작업 중 예상치 못한 오류 발생: {e}")

        print("\n모든 다운로드가 완료될 때까지 10초간 기다립니다...")
        time.sleep(10)

    finally:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] - Download Finish\n")
        print("브라우저를 종료합니다.")
        driver.quit()


if __name__ == "__main__":
    MY_USERNAME = ""
    MY_PASSWORD = ""

    # 다운로드할 목록을 두 가지 형식으로 자유롭게 섞어서 사용하세요.
    DOWNLOAD_LIST = [
        # ["Albeniz"],
        # ["Albinoni"],
        # ["Alkan"],
        # ["Albrechtsberger"],
        # ["Anglebert"],
        # ["Bach, J.S.", "Harpsichord"],
        # ["Bach, J.S.", "Organ"],
        # ["Bach, J.S.", "Lute works"],
        # ["Bach, J.S.", "Chamber music"],
        # ["Bach, J.S.", "Canons"],
        # ["Bach, J.S.", "Various"],
        # ["Bach, J.C."],
        # ["Balbastre"],
        # ["Bartók"],
        # ["Becker"],
        # ["Beethoven", "Chamber music"],
        # ["Beethoven", "Piano"],
        # ["Beethoven", "The Sonatas"],
        # ["Beethoven", "The Variations"],
        # ["Beethoven", "Symphonies"],
        # ["Beethoven", "Fragmented Fugues"],
        # ["Berlioz"],
        # ["Bizet"],
        # ["Boëly"],
        # ["Brade"],
        # ["Brahms"],
        # ["Bruckner"],
        # ["Bühler"],
        # ["Busoni"],
        # ["Buxtehude"],
        # ["Byrd"],
        # ["Cabanilles"],
        # ["Chopin"],
        # ["Cima"],
        # ["Clementi"],
        # ["Couperin"],
        # ["Dandrieu"],
        # ["Danzi"],
        # ["Debussy"],
        # ["Dowland"],
        # ["Dupré"],
        # ["Dussek"],
        # ["Dvořák"],
        # ["Eberl"],
        # ["Eccard"],
        # ["Fauré"],
        # ["Frescobaldi"],
        # ["Franck"],
        # ["Froberger"],
        # ["Führer"],
        # ["Gabrieli, A."],
        # ["Gabrieli, G."],
        # ["Galilei"],
        # ["Gershwin"],
        # ["Gesualdo da Venosa"],
        # ["Glazunov"],
        # ["Glinka"],
        # ["Godowsky"],
        # ["Gomółka"],
        # ["Gorczycki"],
        # ["Gottschalk"],
        # ["Grieg"],
        # ["Guerrero"],
        # ["Hammerschmidt"],
        # ["Handel"],
        # ["Hassler"],
        # ["Haydn, F."],
        # ["Henry VIII"],
        # ["Hindemith"],
        # ["Holborne"],
        # ["Hummel"],
        # ["Isaac"],
        # ["Janáček"],
        # ["Johnson, J.P."],
        # ["Joplin"],
        # ["Karg Elert"],
        # ["Lamb"],
        # ["Lasso"],
        # ["Liszt"],
        # ["Machault"],
        # ["Mahler"],
        # ["Maier"],
        # ["Marcello, B."],
        # ["Marini"],
        # ["Medtner"],
        # ["Mendelssohn-Bartholdy"],
        # ["Merula"],
        # ["Messiaen"],
        # ["Monteverdi"],
        # ["Morales"],
        # ["Morley"],
        # ["Morton"],
        # ["Mozart"],
        # ["Mussorgsky"],
        # ["Pacchioni"],
        # ["Pachelbel, J."],
        # ["Palestrina"],
        # ["Peeters"],
        # ["Poulenc"],
        # ["Praetorius"],
        # ["Pres (Despres)"],
        # ["Prokofiev"],
        # ["Rachmaninov"],
        # ["Ræhs"],
        # ["Raff"],
        # ["Rameau"],
        # ["Ravel"],
        # ["Ravenscroft"],
        # ["Reger"],
        # ["Rimskij-Korsakov"],
        # ["Roman"],
        # ["Rosenmüller"],
        # ["Rossini"],
        # ["Rubinstein"],
        # ["Saint-Saëns"],
        # ["Satie"],
        # ["Scarlatti, D."],
        # ["Schein"],
        # ["Schönberg"],
        # ["Schubert"],
        # ["Schütz"],
        # ["Schumann"],
        # ["Scott"],
        # ["Scriabin"],
        # ["Shostakovich"],
        # ["Sibelius"],
        # ["Soler"],
        # ["Sor"],
        # ["Sousa"],
        # ["Strauss, J. jr."],
        # ["Stravinsky"],
        # ["Tallis"],
        # ["Tchaikovsky"],
        # ["Telemann"],
        # ["Tudor (Henry VIII)"],
        # ["Vecchi"],
        # ["Verdi"],
        # ["Victoria, de"],
        # ["Vierne"],
        # ["Visée"],
        # ["Vivaldi"],
        # ["Wagner"],
        # ["Walther"],
        # ["Widor"],
        # ["Zipoli"],
    ]
    DOWNLOAD_FOLDER = ""
    LOG_FILE_NAME = "error_log.txt"
    # --- 여기까지 수정 --- #

    if MY_USERNAME == "YOUR_USERNAME" or MY_PASSWORD == "YOUR_PASSWORD":
        print(
            "에러: 코드 파일의 MY_USERNAME과 MY_PASSWORD를 실제 아이디와 비밀번호로 변경해주세요."
        )
    else:
        download_midi_files_flexible(
            MY_USERNAME, MY_PASSWORD, DOWNLOAD_LIST, DOWNLOAD_FOLDER, LOG_FILE_NAME
        )
