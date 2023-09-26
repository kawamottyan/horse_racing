## 🐎 Overview
中央競馬及び、地方競馬のレースを予測するためのモデル。

## ⚡️ Quickstart
To get started, follow these steps:

1. **レポジトリをクローン:
   ```
   git clone https://github.com/kawamottyan/horse_racing.git
   ```
2. **ライブラリのインストール:
   ```
   pip install -r requirements.txt
   ```

## 🗂️ Structure
- dataset:データに関するフォルダ
    - data_processing:データの前処理に関するフォルダ
    - scraping_horseracing:netkeibaをスクレイピングするためのフォルダ
    - targetdata:予測するデータを入れるフォルダ
        - rawdata:スクレイピングしたデータを入れるフォルダ
    - traindata:学習データを入れるフォルダ
- models:モデルに関するフォルダ
    - bestmodel:最終モデルをpickleで保存するフォルダ
    - predict.ipynb:最終モデルを使用し予測するファイル

## 📊 Experimental
モデル比較シート:https://docs.google.com/spreadsheets/d/1NDx2BIuMRfIE2A7xMJXyBiNpaLnEC5NBRaZePh3xsGc/edit?usp=sharing
