'''
パラメータの設定
'''
params = {
    'kaisai_nen': '2023',
    'start_date': '1001',
    'end_date': '1101'
}

import psycopg2
import configparser
import pandas as pd
import numpy as np

'''
postgresからデータ取得
'''

# 設定ファイルの読み込み
config = configparser.ConfigParser()
config.read('../config.ini')

user = config['postgresql']['user']
password = config['postgresql']['password']
host = config['postgresql']['host']
database = config['postgresql']['database']

# PostgreSQLに接続
conn = psycopg2.connect(
    dbname=database,
    user=user,
    password=password,
    host=host
)

# SQLクエリの実行
def execute_query(query, params):
    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        return pd.DataFrame(rows, columns=colnames)

# データの取得
n_uma_race_df = execute_query("SELECT * FROM nvd_se WHERE kaisai_nen = %(kaisai_nen)s AND kaisai_tsukihi BETWEEN %(start_date)s AND %(end_date)s", params)
n_race_df = execute_query("SELECT * FROM nvd_ra WHERE kaisai_nen = %(kaisai_nen)s AND kaisai_tsukihi BETWEEN %(start_date)s AND %(end_date)s", params)
n_payout_df = execute_query("SELECT * FROM nvd_hr WHERE kaisai_nen = %(kaisai_nen)s AND kaisai_tsukihi BETWEEN %(start_date)s AND %(end_date)s", params)

'''
データ前処理
'''
# 新しいグループを作成
n_uma_race_df['group'] = n_uma_race_df['kaisai_nen'].astype(int).astype(str) +"-"+ n_uma_race_df['kaisai_tsukihi'].astype(int).astype(str) +"-"+  n_uma_race_df['keibajo_code'].astype(int).astype(str) +"-"+  n_uma_race_df['race_bango'].astype(int).astype(str)
n_race_df['group'] = n_race_df['kaisai_nen'].astype(int).astype(str) +"-"+ n_race_df['kaisai_tsukihi'].astype(int).astype(str) +"-"+  n_race_df['keibajo_code'].astype(int).astype(str) +"-"+  n_race_df['race_bango'].astype(int).astype(str)

# データをマージ
n_race_df = n_race_df.drop(['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'kaisai_kai', 'kaisai_nichime', 'race_bango', 'record_id', 'data_kubun', 'data_sakusei_nengappi'],axis=1)
merged_df = pd.merge(n_uma_race_df, n_race_df, on='group', how='left')

'''
エンコーディング
'''

mapping = {
    'A': '1',
    'B': '2',
    'C': '3',
    'D': '4',
    'E': '5',
    'F': '6',
    'G': '7',
    'H': '8',
}
merged_df['grade_code'] = merged_df['grade_code'].map(mapping).fillna(0)

mapping = {
    'A00': '100',
    'A01': '101',
    'A02': '102',
    'A03': '103',
    'A04': '104',
    'A05': '105',
    'A06': '106',
    'A07': '107',
    'A08': '108',
    'A09': '109',
    'A10': '110',
    'A20': '120',
    'A21': '121',
    'A22': '122',
    'A23': '123',
    'A24': '124',
    'A25': '125',
    'N00': '1400',
    'N01': '1401',
    'N02': '1402',
    'N03': '1403',
    'N04': '1404',
    'N05': '1405',
    'N06': '1406',
    'N07': '1407',
    'N08': '1408',
    'N09': '1409',
    'N10': '1410',
    'N20': '1420',
    'N21': '1421',
    'N22': '1422',
    'N23': '1423',
    'N24': '1424',
    'N25': '1425',
    'N41': '1441',
    'N44': '1444',
    'M00': '1300',
    'M01': '1301',
    'M02': '1302',
    'M03': '1303',
    'M04': '1304',
    'M05': '1305',
}
merged_df['kyoso_kigo_code'] = merged_df['kyoso_kigo_code'].map(mapping).fillna(0)

mapping = {
    'A ': '1',
    'B ': '2',
    'C ': '3',
    'D ': '4',
    }

merged_df['course_kubun'] = merged_df['course_kubun'].map(mapping).fillna(0)

# 欠損値で穴埋め
merged_df['tenko_code'] = np.nan
merged_df['babajotai_code_dirt'] = np.nan
merged_df['shusso_tosu'] = np.nan
merged_df['zogen_ryou'] = np.nan

# データの保存
n_uma_race_df.to_csv('./data/n_uma_race.csv')
n_race_df.to_csv('./data/n_race.csv')
n_payout_df.to_csv('./data/n_payout.csv')
merged_df.to_csv('./data/merged_df.csv')

print(len(merged_df))
print(merged_df.head(5))

# 接続のクローズ
conn.close()
