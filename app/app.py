#インポート
import streamlit as st

#データ加工
import pandas as pd
import re

#モデル
import lightgbm as lgb

#保存
import pickle

#スクレイピング
import requests
from bs4 import BeautifulSoup

#その他
import os
import datetime

# サイドバー
date = st.sidebar.date_input("日付を選択", datetime.date.today())
formatted_date = date.strftime('%Y%m%d')
url = f"https://yoso.netkeiba.com/nar/?pid=race_list&kaisai_date={formatted_date}"

# netkeibaのスクレイピングコード
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
race_lists = soup.find_all('div', class_='RaceList')
race_data = []
for race_list in race_lists:
    venue = race_list.find('div', class_='Jyo').a.text
    races = race_list.find('div', class_='RaceList_Main').find_all('a')
    for race in races:
        race_number = race.find('div', class_='RaceNum').span.text
        race_id = race['href'].split('=')[-1]
        race_data.append({
            '会場': venue,
            'レース番号': race_number,
            'レースID': race_id
        })

###後で消す### 正規表現を用いて、ユーザーの入力値からドメインとrace_idを取得す

def get_url(user_input):
    domain_match = re.search(r'https://(.*?)/', user_input)
    domain = domain_match.group(1) if domain_match else None
    race_id_match = re.search(r'race_id=(\d+)', user_input)
    race_id = race_id_match.group(1) if race_id_match else None
    url = f'https://{domain}/race/shutuba.html?race_id={race_id}'
    return url, race_id

# URLからスクレイピングをするコード

def scraping(url, race_id):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # レースデータ

    race_list = [race_id]  # レースデータを保存するためのリスト
    horse_list_list = []  # 馬データを保存するためのリスト

    title = soup.find('title').text  # レースタイトル
    race_name, date = title.split(' | ')[0], title.split(' | ')[1]
    try:
        extracted_race_name = race_name.split(' ')[0]
        race_list.append(extracted_race_name)
    except:
        race_list.append(race_name)

    match_date = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date)  # 日付
    year, month, day = match_date.groups()
    race_list.append(int(year))
    race_list.append(int(month))
    race_list.append(int(day))

    match_place_race = re.search(r'(\w+)(\d{1,2})R', date)  # 開催場所とレース番号
    place, race_number = match_place_race.groups()
    race_list.append(place)
    race_list.append(int(race_number))

    try:  # 頭数
        race_data_02_element = soup.select_one('.RaceData02')
        if race_data_02_element:
            race_data_02_text = race_data_02_element.get_text()
            horse_count_match = re.search(r'(\d+)頭', race_data_02_text)
            if horse_count_match:
                race_list.append(int(horse_count_match.group(1)))
    except:
        race_list.append(None)

    try:  # レースタイプ
        race_data_element = soup.select_one('.RaceData01')
        if race_data_element:
            race_data_text = race_data_element.get_text()
            ground_match = re.search(r'(ダ|芝)\d+m', race_data_text)
            if ground_match:
                ground_type = ground_match.group(1)
                race_list.append(ground_type)
    except:
        race_list.append(None)

    try:  # 天候と馬場状態
        race_data_element = soup.select_one('.RaceData01')
        if race_data_element:
            race_data_text = race_data_element.get_text()
            weather_match = re.search(r'天候:(\w+)', race_data_text)
            if weather_match:
                race_list.append(weather_match.group(1))
            track_condition_match = re.search(r'馬場:(\w+)', race_data_text)
            if track_condition_match:
                race_list.append(track_condition_match.group(1))
    except:
        race_list.extend([None, None])

    # 馬データ
    cancel_count = 0  # 不参加の競走馬数をカウントするカウンター

    horse_tables = soup.findAll("table", class_="RaceTable01")
    horse_table = horse_tables[0].findAll('tr', class_="HorseList")

    for i in range(len(horse_table)):  # 競走馬数分のループ
        horse_list = [race_id]
        result_row = horse_table[i].findAll("td")

        horse_list.append(result_row[3].get_text().strip())  # 馬名

        if "Cancel" in horse_table[i].get("class"):  # 出場状況
            horse_list.append("取消")
            cancel_count += 1
        else:
            horse_list.append("出走")

        horse_list.append(int(result_row[0].get_text().strip()))  # 枠

        horse_list.append(int(result_row[1].get_text().strip()))  # 番号

        try:
            weight_match = re.match(r'(\d+)\(([-+]?\d+)\)', result_row[8].get_text().strip())  # 馬体重
            body_weight, body_weight_diff = weight_match.groups()
            horse_list.append(float(body_weight))
            horse_list.append(float(body_weight_diff))
        except:
            horse_list.extend([None, None])

        odds = result_row[9].get_text().strip().split('\n')[0]  # オッズ
        cleaned_odds = re.sub(r"[^0-9.]", "", odds)
        if cleaned_odds:
            horse_list.append(float(cleaned_odds))
        else:
            horse_list.append(None)

        popularity = result_row[10].get_text().strip().split('\n')[0]  # 人気
        cleaned_popularity = re.sub(r"[^0-9]", "", popularity)
        if cleaned_popularity:
            horse_list.append(float(cleaned_popularity))
        else:
            horse_list.append(None)

        horse_list_list.append(horse_list)

    # リストからデータフレームを作成する

    race_df = pd.DataFrame(columns = ['race_id','race_title','year', 'month', 'day', 'place', 'race_number', 'total', 'type', 'weather', 'condition'])
    horse_df = pd.DataFrame(columns = ['race_id', 'horse_name', 'mark', 'frame_number','horse_number', 'weight', 'weight_diff', 'odds', 'popular'])
    for horse_list in horse_list_list:
        horse_se = pd.Series( horse_list, index=horse_df.columns)
        horse_df = pd.concat([horse_df, horse_se.to_frame().T], ignore_index=True)
    race_se = pd.Series(race_list, index=race_df.columns )
    race_df = pd.concat([race_df, race_se.to_frame().T], ignore_index=True)

    race_df['total'] = race_df['total'] - cancel_count  # 出場取消頭数分をひく

    return race_df, horse_df

def open_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_file_path = os.path.join(current_dir, 'models', 'model.pkl')
    with open(model_file_path, 'rb') as f:
        model = pickle.load(f)
    return model

def open_df():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    df_file_path = os.path.join(current_dir, 'data', 'merged_df.csv')
    df = pd.read_csv(df_file_path)
    return df

def mapping(race_df, horse_df):
    weather_mapping = {
    '晴': '1',
    '曇': '2',
    '雨': '3',
    '小雨': '4',
    '雪': '5',
    '小雪': '6',
    }
    race_df['tenko_code'] = race_df['weather'].map(weather_mapping)

    condition_mapping = {
        '良': '1',
        '稍': '2',
        '稍重': '2',
        '重': '3',
        '不良': '4',
        }
    race_df['babajotai_code_dirt'] = race_df['condition'].map(condition_mapping)

    condition_mapping = {
        '札幌': '01',
        '函館': '02',
        '福島': '03',
        '新潟': '04',
        '東京': '05',
        '中山': '06',
        '中京': '07',
        '京都': '08',
        '阪神': '09',
        '小倉': '10',
        '門別': '30',
        '北見': '31',
        '岩見沢': '32',
        '帯広': '33',
        '旭川': '34',
        '盛岡': '35',
        '水沢': '36',
        '上山': '37',
        '三条': '38',
        '足利': '39',
        '宇都宮': '40',
        '高崎': '41',
        '浦和': '42',
        '船橋': '43',
        '大井': '44',
        '川崎': '45',
        '金沢': '46',
        '笠松': '47',
        '名古屋': '48',
        '紀三井寺': '49',
        '園田': '50',
        '姫路': '51',
        '益田': '52',
        '福山': '53',
        '高知': '54',
        '佐賀': '55',
        '荒尾': '56',
        '中津': '57',
        '札幌(地方)': '58',
        '函館(地方)': '59',
        '新潟(地方)': '60',
        '中京(地方)': '61'
    }
    race_df['keibajo_code'] = race_df['place'].map(condition_mapping)
    return race_df, horse_df

def choose_race(df, race_df):
    race_df['day'] = race_df['day'].astype(str).str.zfill(2)
    race_df['monthday'] = race_df['month'].astype(str) + race_df['day'].astype(str)
    race_df['group'] = race_df['year'].astype(int).astype(str) +"-"+ race_df['monthday'].astype(int).astype(str) +"-"+  race_df['keibajo_code'].astype(int).astype(str) +"-"+  race_df['race_number'].astype(int).astype(str)
    # df = df[df['group'].isin(race_df['group'])]
    return df, race_df

def merged_df(df, race_df, horse_df):
    # df['tenko_code'] = race_df['tenko_code'].iloc[0]
    # df['babajotai_code_dirt'] = race_df['babajotai_code_dirt'].iloc[0]
    # df['shusso_tosu'] = race_df['total'].iloc[0]

    horse_df = horse_df.rename(columns={
        'horse_name': 'bamei',
        'horse_number': 'umaban',
        'weight': 'bataiju',
        'weight_diff': 'zogen_ryou'
    })

    # horse_df['umaban'] = horse_df['umaban'].astype(int)
    # df['umaban'] = df['umaban'].astype(int)

    # df = df.merge(horse_df[['umaban', 'bataiju']], on='umaban', how='left', suffixes=('', '_new'))
    # df = df.merge(horse_df[['umaban', 'zogen_ryou']], on='umaban', how='left', suffixes=('', '_new'))
    # df['bataiju'] = df['bataiju_new'].combine_first(df['bataiju'])
    # df['zogen_ryou'] = df['zogen_ryou_new'].combine_first(df['zogen_ryou'])
    # df.drop(columns=['bataiju_new', 'zogen_ryou_new'], inplace=True)

    # df['hutan_wariai'] = df['futan_juryo'].astype(int) / pd.to_numeric(df['bataiju'], errors='coerce')

    df = horse_df.copy()

    return df, race_df, horse_df

def convert_datatype(df):
    columns_to_convert = [
                        'umaban',
                        # 'kyori',
                        # 'grade_code',
                        # 'seibetsu_code',
                        # 'moshoku_code',
                        # 'barei',
                        # 'chokyoshi_code',
                        # 'banushi_code',
                        # 'kishu_code',
                        # 'kishu_minarai_code',
                        # 'kyoso_shubetsu_code',
                        # 'juryo_shubetsu_code',
                        # 'shusso_tosu',
                        # 'tenko_code',
                        # 'babajotai_code_dirt',
                        # 'hutan_wariai',
                        'zogen_ryou',

                        # 'track_code',
                        # 'keibajo_code'
                        ]

    for column in columns_to_convert:
        df[column].fillna(0, inplace=True)
        try:
            if df[column].astype(float).apply(lambda x: x.is_integer()).all():
                df[column] = df[column].astype(int)
            else:
                df[column] = df[column].astype(float)
        except ValueError:
            df[column] = df[column].astype(float)

    return df

def prediction(race_df, horse_df):
    df = open_df()
    model = open_model()
    race_df, horse_df = mapping(race_df, horse_df)
    df, race_df = choose_race(df, race_df)
    df, race_df, horse_df = merged_df(df, race_df, horse_df)
    df = convert_datatype(df)

    cancelled_umabans = horse_df[horse_df['mark'] == '取消']['umaban']#出場取消馬を削除
    df = df[~df['umaban'].isin(cancelled_umabans)]

    features = [
            'umaban',
            # 'kyori',
            # 'grade_code',
            # 'seibetsu_code',
            # 'moshoku_code',
            # 'barei',
            # 'chokyoshi_code',
            # 'banushi_code',
            # 'kishu_code',
            # 'kishu_minarai_code',
            # 'kyoso_shubetsu_code',
            # 'juryo_shubetsu_code',
            # 'shusso_tosu',
            # 'tenko_code',
            # 'babajotai_code_dirt',
            # 'hutan_wariai',
            'zogen_ryou',

            # 'track_code',
            # 'keibajo_code'
            ]
    # target = 'kakutei_chakujun'

    df['y_pred'] = model.predict(df[features], num_iteration=model.best_iteration)
    # df['predicted_rank'] = df.groupby('group')['y_pred'].rank(method='min')
    df['predicted_rank'] = df['y_pred'].rank(method='min')

    #データ成形
    # sorted_df = df.sort_values(by=['group', 'predicted_rank'])
    sorted_df = df.sort_values(by=['predicted_rank'])
    sorted_df = sorted_df[['predicted_rank',
                            'bamei',
                            'umaban',
                            # 'bataiju',
                            # 'zogen_ryou',
                            'y_pred']]

    return sorted_df

# アプリケーション

st.markdown(
    """
    <style>
        .sidebar .selectbox {
            font-family: Arial, sans-serif;
        }
        .reportview-container {
            max-width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# サイドバー
st.sidebar.divider()

venues = list(set([data['会場'] for data in race_data]))
selected_venue = st.sidebar.selectbox('会場を選択:', venues)

race_numbers = [data['レース番号'] for data in race_data if data['会場'] == selected_venue]
selected_race_number = st.sidebar.selectbox('レース番号を選択:', race_numbers)

# メイン画面
st.sidebar.divider()
if st.sidebar.button('予測を表示', type='primary' ,use_container_width=True):
    for data in race_data:
        if data['会場'] == selected_venue and data['レース番号'] == selected_race_number:
            url = f"https://nar.netkeiba.com/race/shutuba.html?race_id={data['レースID']}"
            race_id = data['レースID']
            race_df, horse_df = scraping(url, race_id)

            type = race_df['type'].replace({'ダ': 'ダート', '芝': '芝'})
            weather = race_df['weather']
            condition = race_df['condition']

            col1, col2, col3 = st.columns(3)
            col1.metric(label="レース種別", value=type.iloc[0])
            col2.metric(label="天気", value=weather.iloc[0])
            col3.metric(label="馬場状態", value=condition.iloc[0])

            st.divider()
            st.dataframe(race_df)
            st.dataframe(horse_df)
            with st.spinner("予測中..."):
                sorted_df = prediction(race_df, horse_df)


            sorted_df = pd.merge(sorted_df, horse_df[['horse_number','popular','odds']], left_on='umaban', right_on='horse_number', how='left')
            sorted_df.drop('horse_number', axis=1, inplace=True)

            sorted_df = sorted_df.rename(columns={'predicted_rank': '予想順位', 'bamei': '馬名', 'umaban': '馬番', 'y_pred': '予測値', 'popular': '人気順位', 'odds': 'オッズ'})

            max_val = sorted_df['予測値'].max()
            sorted_df['予測値'] = max_val - sorted_df['予測値']

            st.dataframe(
                sorted_df,
                hide_index=True,
                column_config={
                    "予測値": st.column_config.ProgressColumn(
                        "予測値",
                        format="%.2f",
                        min_value=sorted_df['予測値'].min(),
                        max_value=sorted_df['予測値'].max(),
                    ),
                },
            )