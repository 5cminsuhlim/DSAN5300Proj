# %%
# !pip install --no-cache-dir pandas numpy beautifulsoup4 selenium webdriver-manager lxml

# %%
import pandas as pd
import numpy as np
import shutil
import lxml
import lxml.etree
import time
import os
from tqdm import tqdm 

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

import concurrent.futures

# %%
def scrape(regions, seasons, id_anchor):
    data_list = []

    # setup selenium web driver
    service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    for region in regions:
        for season in seasons:
            max_rating = 99999 # arbitrarily high max rating for new season
            page_idx = 0 # start from first page for new season

            while True:
                attempts = 0 # attempts counter
                print(f"Region: {region}, Season: {season}, Fetching page: {page_idx + 1}")
                while attempts < 5:
                    url = f"https://sc2pulse.nephest.com/sc2/?season={season}&queue=LOTV_1V1&team-type=ARRANGED&{region}=true&bro=true&sil=true&gol=true&pla=true&dia=true&mas=true&gra=true&page={page_idx}&type=ladder&ratingAnchor={max_rating}&idAnchor={id_anchor}&count=1#ladder-top"
                    
                    driver.get(url)
                    delay = np.random.uniform(1,3) # adjust based on website tolerance
                    time.sleep(delay)

                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    ladder_table_container = soup.find('div', id='ladder-table-container')
                    if ladder_table_container:
                        tbody = ladder_table_container.find('tbody')
                        rows = tbody.find_all('tr')
                        if rows:
                            for row in rows:
                                player_data = {}
                                player_data['Season'] = season
                                player_data['Region'] = region

                                mmr = int(row.find('td', class_='rating').text.strip())
                                player_data['Rating'] = mmr

                                if mmr >= 4800:
                                    rank = "Grandmaster"
                                elif mmr >= 4250 and mmr < 4800:
                                    rank = "Master"
                                elif mmr >= 3120 and mmr < 4250:
                                    rank = "Diamond"
                                elif mmr >= 2680 and mmr < 3120:
                                    rank = "Platinum"
                                elif mmr >= 2280 and mmr < 2680:
                                    rank = "Gold"
                                elif mmr >= 1720 and mmr < 2280:
                                    rank = "Silver"
                                else:
                                    rank = "Bronze"
                                player_data['Rank'] = rank
                                
                                race_img = row.find('span', class_='race-percentage-entry').find('img', alt=True)
                                player_data['Race'] = race_img['alt'].title() if race_img else 'Random'
                                
                                data_list.append(player_data)

                            break # break out of attempts loop upon success
                        else:
                            attempts += 1
                    else:
                        attempts += 1

                if attempts == 5:
                    print(f"After 5 attempts, no data could be retrieved for season {season}, region {region}, page {page_idx + 1}. Moving on...")
                page_idx += 1
                if page_idx == 3:
                    break

    driver.quit()
    return data_list

# %%
regions = ['us', 'eu', 'kr', 'cn']
total_seasons = np.arange(28, 59) # seasons 28 through 58
season_splits = np.array_split(total_seasons, 4) # split seasons into 2 parts
id_anchors = np.arange(len(season_splits))

# parallelize web scraping
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(scrape, regions, seasons, id_anchor) for seasons, id_anchor in zip(season_splits, id_anchors)]
    
    all_data = []
    for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Scraping Progress"):
        all_data.extend(future.result())

# %%
# organize data by season, region, rank
organized_data = {}

for row in all_data:
    season = row['Season']
    region = row['Region']
    rank = row['Rank']
    
    if season not in organized_data:
        organized_data[season] = {}
    
    if region not in organized_data[season]:
        organized_data[season][region] = {}
        
    if rank not in organized_data[season][region]:
        organized_data[season][region][rank] = []
    
    organized_data[season][region][rank].append(row)

for season, regions in organized_data.items():
    for region, ranks in regions.items():
        # create dirs for each season + region
        directory_path = f"data/ladder/season_{season}/{region}"
        
        # if dir exists, delete
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
        
        # create dirs
        os.makedirs(directory_path)
        
        for rank, rows in ranks.items():
            # convert every row (each list of dictionaries) into df
            df = pd.DataFrame(rows)
            # create csv based on season, region, rank
            filename = f"{directory_path}/{rank}.csv"
            df.to_csv(filename, index=False)
            
'''
31 seasons
4 regions
7 ranks

==> 868 CSVs
'''


