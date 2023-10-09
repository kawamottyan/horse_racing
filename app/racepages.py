import streamlit as st

import pandas as pd
import re
import io

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import os
import time
import requests

# ブラウザの設定
def open_chrome(URL):
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    op.add_argument('--disable-gpu')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options=op)
    wait = WebDriverWait(driver, 3)
    driver.get(URL)
    time.sleep(10)
    wait.until(EC.presence_of_all_elements_located)
    return driver,wait

def get_race_url():
    #保存場所の設定
    TEXT_DIR = "text/"
    if not os.path.isdir(TEXT_DIR):
        os.makedirs(TEXT_DIR)
    else:
        for filename in os.listdir(TEXT_DIR):
            file_path = os.path.join(TEXT_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    CSV_DIR = "csv/"
    if not os.path.isdir(CSV_DIR):
        os.makedirs(CSV_DIR)
    else:
        for filename in os.listdir(CSV_DIR):
            file_path = os.path.join(CSV_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    URL = 'https://nar.netkeiba.com/top/'
    driver, wait = open_chrome(URL)
    # 各レースのURLデータを取得
    li_elements = driver.find_elements(By.CSS_SELECTOR, "li.RaceList_DataItem")
    # 各レースのURLデータを書き込む
    with open(TEXT_DIR+"race.txt", mode='w') as f:
        for li_element in li_elements:
            a_element = li_element.find_element(By.TAG_NAME, "a")
            inner_href = a_element.get_attribute("href")
            # "result" を "shutuba" に変更
            inner_href = inner_href.replace("result", "shutuba")
            parts = inner_href.split('&', 1)
            if len(parts) > 1:
                inner_href = parts[0] + '&rf=race_submenu'
            f.write(inner_href+"\n")
    # ドライバー終了
    driver.quit()
    st.write("対象レースのリストアップ完了")

    combined_df = pd.DataFrame()
    progress_text = st.empty()
    # urlを取得
    with open(TEXT_DIR+"race.txt", "r") as f:
        urls = f.read().splitlines()
        total_iterations = len(urls)
        for i, url in enumerate(urls):
            progress_text.text(f"Iteration {i+1} of {total_iterations} for URL: {url}")
            print(url)
            # 作成するdfの設定
            horse_df = pd.DataFrame(columns=[
                'race_id',
                'race_venue',
                'racenum',
                'year',
                'monthday',
                'frame_number',
                'horse_number',
                'style',
            ])

            driver, wait = open_chrome(url)
            url = driver.current_url
            race_id = url.split("=")[1].split("&")[0]
            response = requests.get(url)
            response.encoding = response.apparent_encoding
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            # レース情報のスクレイピング
            title = soup.find('title').text
            race_name, date = title.split(' | ')[0], title.split(' | ')[1]
            year = date.split("年")[0]
            monthday = date.split("年")[1].split("月")[0] + date.split("月")[1].split("日")[0]
            race_venue = soup.find("div", class_="RaceData02").get_text().split("\n")[2]
            try:
                racenum = soup.find("span", class_="RaceNum").get_text().strip().replace("R", "")
            except AttributeError:
                racenum_match = re.search(r'(\d+R)', title)
                if racenum_match:
                    racenum = racenum_match.group(1).replace("R", "")
                else:
                    racenum = "不明"
            # 脚質情報のテーブルを取得
            style_table = soup.find("table", class_="RaceCommon_Table Kyaku_Type")
            # 脚質と馬番のマッピングを格納する辞書
            style_mapping = {}
            # 各脚質のセクションをループ
            for row in style_table.find_all("tr"):
                style_name = row.find("th").get_text()
                numbers = row.find_all("span", class_="Kyaku_Type_Num")
                for number in numbers:
                    style_mapping[number.get_text()] = style_name
            horse_tables = soup.findAll("table", class_="RaceTable01")
            horse_table = horse_tables[0].findAll('tr', class_="HorseList")
            horse_list_list = []

            # tableの情報から各情報を抜き出す
            for i in range(len(horse_table)):
                horse_list = [race_id, race_venue, racenum, year, monthday]
                result_row = horse_table[i].findAll("td")
                horse_list.append(result_row[0].get_text())  # 枠
                horse_number = result_row[1].get_text()  # 番号
                horse_list.append(horse_number)
                horse_list.append(style_mapping.get(horse_number, "不明"))
                horse_list_list.append(horse_list)
            for horse_list in horse_list_list:
                horse_se = pd.Series(horse_list, index=horse_df.columns)
                horse_df = pd.concat([horse_df, horse_se.to_frame().T], ignore_index=True)
            csv_file_path = os.path.join(CSV_DIR, f"{race_id}.csv")
            horse_df.to_csv(csv_file_path, index=False, encoding='utf-8')

            # ドライバー終了
            driver.quit()

    # ディレクトリが存在するか確認
    if os.path.isdir(CSV_DIR):
        # ディレクトリ内のすべてのファイルをリストアップ
        for filename in os.listdir(CSV_DIR):
            file_path = os.path.join(CSV_DIR, filename)
            # CSVファイルであれば読み込み
            if os.path.isfile(file_path) and filename.endswith('.csv'):
                df = pd.read_csv(file_path)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
    csv = combined_df.to_csv(index=False, encoding='utf-8')
    csv.to_csv("../targetdata/rawdata/n_style.csv", index=False, encoding='utf-8')
    b_csv = csv.encode()
    st.write("CSV作成完了")
    return b_csv

# StreamlitのUI部分
st.title("今日の地方競馬レース展開予想の取得")

# スクレイピング開始ボタン
if st.button("スクレイピング開始"):
    with st.spinner("スクレイピング中..."):
        b_csv = get_race_url()
    st.success("スクレイピングが完了しました。")
    st.download_button(
        label="Download CSV File",
        data=io.BytesIO(b_csv),
        file_name="n_style.csv",
        mime="text/csv"
    )