from splinter import Browser
from bs4 import BeautifulSoup as bs
import pandas as pd
import pymongo
from pprint import pprint
from datetime import datetime
import re
from bson.objectid import ObjectId
import os



cacheFilePath = "./../../music_project_caches/_schedule_playlist.txt"
if os.path.isfile(cacheFilePath):
    with open(cacheFilePath, encoding='utf-8') as cacheFile:
        html = cacheFile.read()
else:
    executable_path = {'executable_path': '/Users/soria/Anaconda3/Scripts/chromedriver'}
    browser = Browser('chrome', **executable_path)
    url = "https://spinitron.com/radio/playlist.php?station=kdhx&show=schedule&sv=l#here"
    browser.is_element_present_by_css("p.plhead", wait_time=1)
    browser.visit(url)
    html = browser.html
    browser.quit()
    with open(cacheFilePath, "w", encoding='utf-8') as cacheFile:
        cacheFile.write(html)

schedule_soup = bs(html, 'html.parser')
schedule_tables = schedule_soup.find_all('tbody')
schedule_tables = schedule_tables[2:9]

program_url_list = []
for day in schedule_tables:
    day_list = []
    day_list = day.find_all('p', class_='showname')
    for program in day_list:
        print(program)
        program_url_list.append('https://spinitron.com/radio/' + program.find('a')['href'])


print(program_url_list)