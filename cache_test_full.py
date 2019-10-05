import pandas as pd
import pymongo
from pprint import pprint
from datetime import datetime
import re
import os

import pymongo
from bson.json_util import dumps, loads
from bson.objectid import ObjectId

from splinter import Browser
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.common.exceptions import TimeoutException


script_start = datetime.now()

def dateFixer(str):
    if str == '':
        return ['', '', '', '']
    else:
        date_list = []
        str = re.sub(r'[.]', ':', str)
        parts = str.split()
        parts[2] = parts[2].strip("stndrh")
        str = " ".join(parts)
        date = re.search(r'^(.*?)\d\d\d\d', str).group(0)
        start_time = re.search(r'.+?(?=–)', str).group(0)
        end_time = date + " " + re.search(r'(?<=–).*', str).group(0)
        start_dt_obj = datetime.strptime(start_time, '%a %b %d %Y %I:%M%p')
        end_dt_obj = datetime.strptime(end_time, '%a %b %d %Y %I:%M%p')
        date_list.append(start_time)
        date_list.append(start_dt_obj)
        date_list.append(end_time)
        date_list.append(end_dt_obj)
        date_list.append(date)
        return date_list

# executable_path = {'executable_path': '/Users/soria/Anaconda3/Scripts/chromedriver'}
# executable_path = {'executable_path': '/Users/soria/Anaconda3/Scripts/chromedriver'}
# browser = Browser('chrome', **executable_path)

conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)
db = client.kdhx
# collection = db.urls_test
collection = db.urls
if collection.find_one():
    # test_programs = collection.find_one()
    # del test_programs['_id']
    # program_name_list = [k for k, v in test_programs.items()]
    kdhx_programs = collection.find_one()
    del kdhx_programs['_id']
    program_name_list = [k for k, v in kdhx_programs.items()]
else:

    # Get genres of each program and write to dictionary, match character cases
    # cacheFilePath = "./../../music_project_caches/_schedule_genre.txt"
    cacheFilePath = "./../../Caches/music_project_caches/_schedule_genre.txt"
    if os.path.isfile(cacheFilePath):
        with open(cacheFilePath, encoding='utf-8') as cacheFile:
            html = cacheFile.read()
    else:
        url = 'http://kdhx.org/shows/schedule'
        driver = webdriver.Chrome()
        driver.get(url)
        html = driver.page_source
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "show-schedule"))
            )
        finally:
            driver.quit()          
        with open(cacheFilePath, "w", encoding='utf-8') as cacheFile:
            cacheFile.write(html)

    schedule_soup = bs(html, 'html.parser')

    weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    kdhx_genres = {}
    for day in weekdays:
        schedule = schedule_soup.find('div', class_='day', dow=day).find_all('a')
        program_list = []
        for item in schedule:
            program = item.find('div', class_='show-title').find('span', style='margin-right:5px').get_text().strip()
            program_list.append(program)
            #print(program)
            try:
                program = re.search(r'.+?(?=\s\s)', program).group(0)
            except:
                program = program
            kdhx_genres.setdefault(program, {})
            genre_elements = item.find('div', class_='show-genres').find_all('span')
            counter = 0
            for element in genre_elements:
                counter += 1
                countStr = str(counter)
                kdhx_genres[program].setdefault(countStr, {})
                kdhx_genres[program][countStr] = element.get_text()

    kdhx_genres['RSVP'] = kdhx_genres.pop('R.S.V.P.')
    kdhx_genres['No Time To Tarry Here'] = kdhx_genres.pop('No Time to Tarry Here')
    kdhx_genres['Music from the Hills'] = kdhx_genres.pop('Music From the Hills')
    kdhx_genres['Boogie On Down'] = kdhx_genres.pop('Boogie on Down')
    kdhx_genres['Howzit Bayou'] = kdhx_genres.pop('Howzit Bayou?')
    kdhx_genres['Cure For Pain'] = kdhx_genres.pop('Cure for Pain')
    kdhx_genres["Shake 'em on Down"] = kdhx_genres.pop("Shake 'Em on Down")

    collection = db.genres
    collection.insert_one(kdhx_genres)
    # code to get playlists

    # cacheFilePath = "./../../music_project_caches/_schedule_playlist.txt"
    cacheFilePath = "./../../Caches/music_project_caches/_schedule_playlist.txt"

    if os.path.isfile(cacheFilePath):
        with open(cacheFilePath, encoding='utf-8') as cacheFile:
            html = cacheFile.read()
    else:
        url = "https://spinitron.com/KDHX/calendar#here"
        driver = webdriver.Chrome()
        driver.get(url)
        html = driver.page_source
        # try:
        #     element = WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located((By.ID, "calendar-w0"))
        #     )
        # finally:
            # driver.quit()          
        html = driver.page_source
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
            program_url_list.append('https://spinitron.com/radio/' + program.find('a')['href'])

    kdhx_programs = {}
    test_programs = {}

    program_names = [x for x in kdhx_genres.keys()]
    for index, program_url in enumerate(program_url_list):
    #     print(program_url)
        name = re.sub( r'[\s]', '_', program_names[index])
        name = re.sub( r'[?]', '', name)
        cacheFilePath = f"./../../Caches/music_project_caches/_playsists_{name}.txt"
        # cacheFilePath = f"./../../music_project_caches/_playlists_{name}.txt"
        if os.path.isfile(cacheFilePath):
            with open(cacheFilePath, encoding='utf-8') as cacheFile:
                html = cacheFile.read()
        else:
            driver = webdriver.Chrome()
            driver.get(program_url)
            html = driver.page_source
            with open(cacheFilePath, "w", encoding='utf-8') as cacheFile:
                cacheFile.write(html)
        program_soup = bs(html, 'html.parser')
        program_name = program_soup.find('p', class_='plhead').get_text()
        kdhx_programs.setdefault(program_name, {})
        kdhx_programs[program_name].setdefault('program_url', program_url)
        kdhx_programs[program_name].setdefault('genre(s)', {})
        kdhx_programs[program_name].setdefault('playlist(s)', {})
        test_programs.setdefault(program_name, {})
        test_programs[program_name].setdefault('program_url', program_url)
        test_programs[program_name].setdefault('genre(s)', {})
        test_programs[program_name].setdefault('playlist(s)', {})
        playlist_table = program_soup.find('table', id='pltable')
        playlist_anchors = playlist_table.find_all('a', title='Click for the playlist')
        playlist_anchors = playlist_anchors[::-1]
        counter = 0
        for index, anchor in enumerate(playlist_anchors):
            if index % 2 == 0:
                counter += 1
                countStr = str(counter)
                url = 'https://spinitron.com/radio/' + playlist_anchors[index]['href']
                print(url)
                kdhx_programs[program_name]['playlist(s)'].setdefault(countStr, {})
                kdhx_programs[program_name]['playlist(s)'][countStr] = url
        for index, anchor in enumerate(playlist_anchors[::80]):
            if index % 2 == 0:
                counter += 1
                countStr = str(counter)
                url = 'https://spinitron.com/radio/' + playlist_anchors[index]['href']
                test_programs[program_name]['playlist(s)'].setdefault(countStr, {})
                test_programs[program_name]['playlist(s)'][countStr] = url

    program_name_list = [k for k, v in kdhx_programs.items()]
    for program in program_name_list:
        test_programs[program]['genre(s)'] = kdhx_genres[program]

    for program in program_name_list:
        kdhx_programs[program]['genre(s)'] = kdhx_genres[program]

    collection = db.urls
    collection.insert_one(kdhx_programs)
    collection = db.urls_test
    collection.insert_one(test_programs)



for program in program_name_list[0:3]:
    main_df = pd.DataFrame({'program': '', 'dj': '', 'start_time': '', 'start_dt_object': '', 'end_time': '',
                        'end_dt_object': '', 'genre(s)': '', 'description': '', 'play_time': '', 'play_time_obj': '',       
                        'artist': '', 'artist_url': '', 'track': '', 'album': '', 'album_url': '', 'label': '', 
                        'label_url': '', 'type': '', 'notes': '', 'play_duration': ''}, index=[x for x in range(0)])
    loop_timer = [datetime.now()]
    counter = 0
    kdhx_dict = {}
    times = []
    averages = []
    # for index, playlist_url in test_programs[program]['playlist(s)'].items():
    for dict_index, playlist_url in kdhx_programs[program]['playlist(s)'].items():
        begin_loop = datetime.now()
        loop_timer.append(begin_loop)
        name = re.sub(r'[\s]', '_', program)
        cacheFilePath = f"./../../Caches/music_project_caches/{name}_{dict_index}.txt"
        # cacheFilePath = f"./../../music_project_caches/{name}_{dict_index}.txt"
        if os.path.isfile(cacheFilePath):
            with open(cacheFilePath, encoding='utf-8') as cacheFile:
                html = cacheFile.read()
        else:
            driver = webdriver.Chrome()
            driver.get(playlist_url)
            html = driver.page_source
            with open(cacheFilePath, "w", encoding='utf-8') as cacheFile:
                cacheFile.write(html)
        # print(f"{program} {dict_index} of {len(test_programs[program]['playlist(s)'])}: {playlist_url}")
        print(f"{program} {dict_index} of {len(kdhx_programs[program]['playlist(s)'])}: {playlist_url}")
        time = begin_loop - loop_timer[counter]
        times.append(time.total_seconds())
        average = sum(times)/len(times)
        averages.append(average)
        print(f"Previous loop took: {time} -- Averaging: {average} -- Diff: {time.total_seconds() - average}")
        counter += 1
        playlist_soup = bs(html, 'html.parser')
        try:
            if playlist_soup.find('p', class_='plhead').find('a').get_text() == ('Chicken Shack' or 'Chicken Shack Alley'):
                program_name = 'Chicken Shack'
            else:
                program_name = playlist_soup.find('p', class_='plhead').find('a').get_text()
        except:
            program_name = ''
        collection = db[program_name]
        try:
            play_date = playlist_soup.find('p', class_='plheadsub').get_text()
        except:
            play_date = ''
        try:
            dj = playlist_soup.find('div', class_='infoblock').find('p', class_='plhead').find('a').get_text()
            dj = re.sub(r'[.]', '', dj)
        except:
            dj = ''
        start_time = dateFixer(play_date)[0]
        start_dto = dateFixer(play_date)[1]
        end_time = dateFixer(play_date)[2]
        end_dto = dateFixer(play_date)[3]
        date = dateFixer(play_date)[4]
        kdhx_dict.setdefault(program_name, {})
        try:
            kdhx_dict[program_name]['description'] = playlist_soup.find('div', id='playlisthead').find('p', class_='indent').get_text()
        except:
            kdhx_dict[program_name]['description'] = ""
        kdhx_dict[program_name]['genre(s)'] = kdhx_programs[program]['genre(s)']
        # kdhx_dict[program_name]['genre(s)'] = test_programs[program]['genre(s)']
        kdhx_dict[program_name].setdefault(dict_index, {}).setdefault(dj, {})
        kdhx_dict[program_name][dict_index]['start_time'] = start_time
        kdhx_dict[program_name][dict_index]['start_dt_object'] = start_dto
        kdhx_dict[program_name][dict_index]['end time'] = end_time
        kdhx_dict[program_name][dict_index]['end_dt_object'] = end_dto
        play_dict = {}
        playlist_div = playlist_soup.find('div', class_='plblock')
        play_divs = playlist_div.find_all('div', class_='f2row')
        for index, play in enumerate(play_divs):
            try:
                play_time = play.find('p', class_='st').get_text()
                play_time_obj = datetime.strptime(date + " " + play_time, '%a %b %d %Y %I:%M%p')
            except:
                play_time = '' 
                play_time_obj = ''
            try:
                if index == len(play_divs) - 1:
                    time_delta = datetime.strptime(re.search(r'(?<=\d\d\d\d\s).*', end_time).group(0), '%I:%M%p') - datetime.strptime(play_time,'%I:%M%p')
                else:
                    time_delta = datetime.strptime(play_divs[index+1].find('p', class_='st').get_text(),'%I:%M%p') - datetime.strptime(play_time,'%I:%M%p')
                play_duration = time_delta.total_seconds() / 60
            except:
                play_duration = ''
            kdhx_dict[program_name][dict_index][dj].setdefault(play_time, {})
            play_dict = {'artist': '', 'artist_url': '', 'track': '', 'album': '', 'album_url': '',    
                         'label': '', 'label_url': '', 'type': '', 'notes': '', 'play_duration': '', 'play_time_obj': ''}
            play_dict['play_time_obj'] = play_time_obj
            play_dict['play_duration'] = play_duration
            try:
                play_dict['artist'] = play.find('span', class_='aw').get_text()
            except:
                play_dict['artist'] = ''
            try:
                play_dict['artist_url'] = "https://spinitron.com/radio/" + play.find('span', class_='aw').find('a')['href']
            except:
                play_dict['artist_url'] = ''
            try:
                play_dict['track'] = play.find('span', class_='sn').get_text()
            except:
                play_dict['track'] = ''
            try:
                play_dict['album'] = play.find('span', class_='dn').get_text()
            except:
                play_dict['album'] = ''
            try:
                play_dict['album_url'] = "https://spinitron.com/radio/" + play.find('span', class_='dn').find('a')['href']
            except:
                play_dict['album_url'] = ''
            try:
                play_dict['label'] = play.find('span', class_='ld').get_text()
            except:
                play_dict['label'] = ''
            try:
                play_dict['label_url'] = "https://spinitron.com/radio/" + play.find('span', class_='ld').find('a')['href']
            except:
                play_dict['label_url'] = ''
            try:
                play_dict['type'] = play.find('span', class_='fg').get_text()
            except:
                play_dict['type'] = ''
            try:
                play_dict['notes'] = play.find('span', class_='so').get_text()
            except:
                play_dict['notes'] = ''
            kdhx_dict[program_name][dict_index][dj][play_time] = play_dict
        collection.update_one({}, {'$set': kdhx_dict}, upsert=True)
        for index, play in enumerate(play_divs):
            this_df = pd.DataFrame({'program': '', 'dj': '', 'start_time': '', 'start_dt_object': '', 'end_time': '',
                            'end_dt_object': '', 'genre(s)': '', 'description': '', 'play_time': '', 'play_time_obj': '',       
                            'artist': '', 'artist_url': '', 'track': '', 'album': '', 'album_url': '', 'label': '', 
                            'label_url': '', 'type': '', 'notes': '', 'play_duration': ''}, index=[x for x in range(1)])
            try:
                play_time = play.find('p', class_='st').get_text()
                play_time_obj = datetime.strptime(date + " " + play_time, '%a %b %d %Y %I:%M%p')
            except:
                play_time = ''
                play_time_obj = ''
            try:
                if index == len(play_divs) - 1:
                    time_delta = datetime.strptime(re.search(r'(?<=\d\d\d\d\s).*', end_time).group(0), '%I:%M%p') - datetime.strptime(play_time,'%I:%M%p')
                else:
                    time_delta = datetime.strptime(play_divs[index+1].find('p', class_='st').get_text(),'%I:%M%p') - datetime.strptime(play_time,'%I:%M%p')
                play_duration = time_delta.total_seconds() / 60
            except:
                play_duration = ''
            try:
                dj = playlist_soup.find('div', class_='infoblock').find('p', class_='plhead').find('a').get_text()
                dj = re.sub(r'[.]', '', dj)
            except:
                dj = ''
            for index, row in this_df.iterrows():
                this_df.loc[index, 'program'] = program_name
                this_df.loc[index, 'dj'] = dj
                this_df.loc[index, 'start_time'] = start_time
                this_df.loc[index, 'start_dt_object'] = start_dto
                this_df.loc[index, 'end_time'] = end_time
                this_df.loc[index, 'end_dt_object'] = end_dto
                # this_df.loc[index, 'genre(s)'] = test_programs[program]['genre(s)'].values()
                this_df.loc[index, 'genre(s)'] = kdhx_programs[program]['genre(s)'].values()
                try:
                    this_df.loc[index, 'description'] = playlist_soup.find('div', id='playlisthead').find('p', class_='indent').get_text()
                except:
                    this_df.loc[index, 'description'] = ""
                this_df.loc[index, 'play_time'] = play_time
                this_df.loc[index, 'play_time_obj'] = play_time_obj
                this_df.loc[index, 'play_duration'] = play_duration
                try:
                    this_df.loc[index, 'artist'] = play.find('span', class_='aw').get_text()
                except:
                    this_df.loc[index, 'artist'] = ''
                try:
                    this_df.loc[index, 'artist_url'] = "https://spinitron.com/radio/" + play.find('span', class_='aw').find('a')['href']
                except:
                    this_df.loc[index, 'artist_url'] = ''
                try:
                    this_df.loc[index, 'track'] = play.find('span', class_='sn').get_text()
                except:
                    this_df.loc[index, 'track'] = ''
                try:
                    this_df.loc[index, 'album'] = play.find('span', class_='dn').get_text()
                except:
                    this_df.loc[index, 'album'] = ''
                try:
                    this_df.loc[index, 'album_url'] = "https://spinitron.com/radio/" + play.find('span', class_='dn').find('a')['href']
                except:
                    this_df.loc[index, 'album_url'] = ''
                try:
                    this_df.loc[index, 'label'] = play.find('span', class_='ld').get_text()
                except:
                    this_df.loc[index, 'label'] = ''
                try:
                    this_df.loc[index, 'label_url'] = "https://spinitron.com/radio/" + play.find('span', class_='ld').find('a')['href']
                except:
                    this_df.loc[index, 'label_url'] = ''
                try:
                    this_df.loc[index, 'type'] = play.find('span', class_='fg').get_text()
                except:
                    this_df.loc[index, 'type'] = ''
                try:
                    this_df.loc[index, 'notes'] = play.find('span', class_='so').get_text()
                except:
                    this_df.loc[index, 'notes'] = ''
            main_df = pd.concat([main_df, this_df])
    main_df = main_df.reset_index().drop(columns='index')
    name = re.sub( r'[\s]', '_', program)
    name = re.sub( r'[?]', '', name)
    main_df.to_csv(f"./../../music_project_data/{name}.csv")
    script_end = datetime.now()
    logFilePath = "./../../music_project_data/log.txt"
    with open(logFilePath, "a", encoding='utf-8') as logFile:
        logFile.write(f"Script for {program}\n\r"
                    f"Script Start: {script_start}\n\r"
                    f"Script End: {script_end}\n\r"
                    f"Script Duration: {script_end - script_start}\n\r"
                    f"Average Loop Time: {sum(averages)/len(averages)}(s)\n\r"
                    f"===========================================\n\r")
    print(f"Script for:{program}")
    print(f"Script Start:{script_start}")
    print(f"Script End:{script_end}")
    print(f"Script Duration:{script_end - script_start}")
    print(f"Average Loop Time: {sum(averages)/len(averages)}")
driver.quit()




import os

print("Path at terminal when executing this file")
print(os.getcwd() + "\n")

print("This file path, relative to os.getcwd()")
print(__file__ + "\n")

print("This file full path (following symlinks)")
full_path = os.path.realpath(__file__)
print(full_path + "\n")

print("This file directory and name")
path, filename = os.path.split(full_path)
print(path + ' --> ' + filename + "\n")

print("This file directory only")
print(os.path.dirname(full_path))