# import streamlit as st
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By
# from bs4 import BeautifulSoup

# def get_driver():
#     return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# options = Options()
# options.add_argument('--disable-gpu')
# options.add_argument('--headless')

# driver = get_driver()
# driver.get("https://nar.netkeiba.com/top/")
# html = driver.page_source
# driver.quit()
# soup = BeautifulSoup(html, 'html.parser')

# # race_numbers = [div.text.strip() for div in soup.select('div.Race_Num > span')]
# # venues = [li.a.text.strip() for li in soup.select('ul.RaceList_ProvinceSelect li')]

import streamlit as st

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@st.cache_resource
def scraping():
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--headless')

driver = scraping()
driver.get("http://example.com")

st.code(driver.page_source)