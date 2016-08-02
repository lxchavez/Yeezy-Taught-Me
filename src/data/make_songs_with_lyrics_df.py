# -*- coding: utf-8 -*-
import os
import sys
import logging
import numpy as np
import pandas as pd
import time
import glob
import datetime
import sqlite3
from dotenv import find_dotenv, load_dotenv

src_dir = os.path.join(os.getcwd(), os.pardir, 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)
import Util

# User defined variables
# To-Do: refactor to config file
#################################
BASE_PATH               = '/home/ec2-user/notebook/projects/Yeezy-Taught-Me/'
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

def get_all_songs_df():
    query = "SELECT * FROM songs"
    songs_df = Util.execute_query(msd_subset_addf_path,TRACK_METADATA_DB, query)
    return songs_df

def find_valid_file(basedir, track_id, callback=lambda x: x, ext='.h5'):
    for root, dirs, files in os.walk(basedir):
        for file in files:
            if file.endswith(ext) and track_id in file:
                callback(os.path.join(root, file))

def get_lyrics(artist_name, song_title):
    song = Util.Song(artist=artist_name, title=song_title)
    lyrics = song.lyricwikia()
    return lyrics

def export_dataset(df, filename):
    df.to_pickle(os.path.join(OUTPUT_PATH, filename))

def main():
    logger = logging.getLogger(__name__)
    logger.info('Creating songs_with_lyrics_df data set from raw data')
    
    # Get all songs
    songs_with_lyrics_df = get_all_songs_df()
    songs_with_lyrics_df['lyrics'] = songs_with_lyrics_df.apply(
        lambda row: get_lyrics(row['artist_name'], row['title']), axis=1)

    export_dataset(songs_with_lyrics_df, 'songs_with_lyrics_df.pkl')

    logger.info('Done!')

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()

