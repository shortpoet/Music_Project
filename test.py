import pandas as pd
from datetime import datetime

all_url_df = pd.read_csv("all_playlist_urls.csv")

all_url_list = all_url_df['0'].tolist()

length = len(all_url_list)

print(length)

for index, url in enumerate(all_url_list):
    if url == 'https://spinitron.com/radio/playlist.php?station=kdhx&sv=l&playlist=62343#here':
        print(index)

print(datetime.now())