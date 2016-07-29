# -*- coding: utf-8 -*-
import os
import click
import logging
import numpy as np
import pandas as pd
import sys
import time
import glob
import datetime
import sqlite3
from dotenv import find_dotenv, load_dotenv

# User defined variables
# To-Do: refactor to config file
#################################
BASE_PATH               = '/home/ec2-user/notebook/projects/Yeezy-Taught-Me/'
KANYE_WEST_ARTIST_ID    = 'ARRH63Y1187FB47783'
ARTIST_SIMILARITY_DB    = 'subset_artist_similarity.db'
ARTIST_TERM_DB          = 'subset_artist_term.db'
TRACK_METADATA_DB       = 'subset_track_metadata.db'

## Define files
################
# Our output path for the data set
OUTPUT_PATH             = '/home/ec2-user/notebook/projects/Yeezy-Taught-Me/data/interim/'
# path to the Million Song Dataset subset (uncompressed)
msd_subset_path         = os.path.join(BASE_PATH, 'data/raw/MillionSongSubset')
# path to the Million Song Helper Code
msd_code_path           = os.path.join(BASE_PATH, 'src/MSongsDB')
# path to the MSD files
msd_subset_data_path    = os.path.join(msd_subset_path, 'data')
msd_subset_addf_path    = os.path.join(msd_subset_path, 'AdditionalFiles')

# imports specific to the MSD
path = os.path.join(msd_code_path, 'PythonSrc')
if path not in sys.path:
    sys.path.append(path)
import hdf5_getters as GETTERS

def execute_query(db_name, query):
    ### Returns a DataFrame containing the query results
    # Read sqlite query results into a pandas DataFrame
    con = sqlite3.connect(os.path.join(msd_subset_addf_path, db_name))
    df = pd.read_sql_query(query, con)
    con.close()
    return df

def get_kanye_terms():
    query = "SELECT DISTINCT term FROM artist_term WHERE artist_id = '{0}'".format(KANYE_WEST_ARTIST_ID)
    df = execute_query(ARTIST_TERM_DB, query)
    return set(df['term'])

def get_all_artist_terms(kanye_terms):
    query = "SELECT * FROM artist_term"
    all_artists_terms_df = execute_query(ARTIST_TERM_DB, query)
    mask = all_artists_terms_df['term'].isin(kanye_terms)
    return all_artists_terms_df.loc[mask]

def get_compare_songs_df(all_artists_terms_df):
    query = "SELECT * FROM songs"
    songs_df = execute_query(TRACK_METADATA_DB, query)
    same_terms_artists_set = set(all_artists_terms_df['artist_id'])
    mask = songs_df['artist_id'].isin(same_terms_artists_set)
    return songs_df.loc[mask].copy(deep=True)

def find_valid_file(basedir, track_id, callback=lambda x: x, ext='.h5'):
    songs_with_features = list()
    for root, dirs, files in os.walk(basedir):
        for file in files:
            if file.endswith(ext) and track_id in file:
                features_dict = callback(os.path.join(root, file))
                songs_with_features.append(features_dict)
    
    song_features_df = pd.DataFrame(songs_with_features)
    song_features_df.to_pickle(os.path.join(OUTPUT_PATH, 'song_features_df.pkl'))

def get_features(filename):
    song_dict = dict()
    
    # Open the file
    h5 = GETTERS.open_h5_file_read(filename)
            
    # Create a dictionary entry and add it to our song list
    getter_props = (name for name in dir(GETTERS) if name.startswith('get_'))
    for prop in getter_props:
        key = prop.replace('get_', '')
        value = getattr(GETTERS, prop)(h5)
        song_dict[key] = value
                                                                
    # Close the file!
    h5.close()

    return song_dict

#@click.command()
#@click.argument('input_filepath', type=click.Path(exists=True))
#@click.argument('output_filepath', type=click.Path())
def main():
    logger = logging.getLogger(__name__)
    logger.info('Making songs_features_df data set from raw data')
    
    # Grab Kanye terms
    kanye_terms = get_kanye_terms()

    # Grab terms for all the other artists
    all_artists_terms_df = get_all_artist_terms(kanye_terms)

    # Get all songs from the artist_id's we know that share terms with Kanye
    compare_songs_df = get_compare_songs_df(all_artists_terms_df)
    compare_songs_df['track_id'].apply(
        lambda x: find_valid_file(msd_subset_data_path, x, callback=get_features))

    logger.info('Done!')

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()

