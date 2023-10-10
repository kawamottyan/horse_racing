import streamlit as st
import requests
from bs4 import BeautifulSoup

url = 'https://yoso.netkeiba.com/nar/?pid=race_list'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# すべてのレースリストを取得
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

venues = list(set([data['会場'] for data in race_data]))
selected_venue = st.selectbox('会場を選択:', venues)

race_numbers = [data['レース番号'] for data in race_data if data['会場'] == selected_venue]
selected_race_number = st.selectbox('レース番号を選択:', race_numbers)

if st.button('URLを表示'):
    for data in race_data:
        if data['会場'] == selected_venue and data['レース番号'] == selected_race_number:
            st.write(f"https://yoso.netkeiba.com/nar/?pid=race_yoso_list&race_id={data['レースID']}")