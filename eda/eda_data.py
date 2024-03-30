import os
import pandas as pd

data_directory = '../data/data_web' 
all_data = []

#data processing and cleaning
#iterate over each season
for season_dir in os.listdir(data_directory):
    season_path = os.path.join(data_directory, season_dir)

    if os.path.isdir(season_path):
        #iterate over each region within the season
        for region_dir in os.listdir(season_path):
            region_path = os.path.join(season_path, region_dir)
            
            #iterate over each rank csv file within the region
            for rank_file in os.listdir(region_path):
                if rank_file.endswith('.csv'):
                    file_path = os.path.join(region_path, rank_file)
                    rank_name = rank_file.replace('.csv', '')
                    
                    #read the data file and add the season, region, and rank
                    data = pd.read_csv(file_path)
                    data['Season'] = season_dir.replace('season_', '')
                    data['Region'] = region_dir
                    data['Rank'] = rank_name
                    
                    #append the dataset to the list
                    all_data.append(data)

#combine all data into a single dataset
combined_data = pd.concat(all_data, ignore_index=True)

#save data
#data_directory = './data/data_web' 
#output_directory = './data'
#output_path = os.path.join(output_directory, 'combined_data.csv')
#combined_data.to_csv(output_path, index=False)

#import pandas as pd
#from bokeh.plotting import figure, show, output_file
#from bokeh.models import ColumnDataSource, Select, CustomJS
#from bokeh.layouts import column

#calculate the percentage of players for each race
percentage_data = combined_data.groupby(['Season', 'Region', 'Rank', 'Race']).size().reset_index(name='Count')
total_counts = percentage_data.groupby(['Season', 'Region', 'Rank'])['Count'].transform('sum')
percentage_data['Percentage'] = (percentage_data['Count'] / total_counts) * 100

#save data
#output_path = os.path.join(output_directory, 'percentage_data.csv')
#percentage_data.to_csv(output_path, index=False)