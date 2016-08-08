#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ConfigParser
import os
import sys

# Load the configuration file
#################################

config = ConfigParser.ConfigParser()
project_config_dir = os.path.join(os.getcwd(), 'src/data/project_config.ini')
config.read(project_config_dir)

# Read in project config variables
###################################

ARTIST_SIMILARITY_DB    = config.get('project', 'artist_similarity_db')
ARTIST_TERM_DB          = config.get('project', 'artist_term_db')
TRACK_METADATA_DB       = config.get('project', 'track_metadata_db')
TARGET_ARTIST_ID        = config.get('artist', 'target_artist_id')
OUTPUT_PATH             = config.get('output', 'interim')

## Define MSD code and data file paths
#######################################

# path to the Million Song Dataset subset (uncompressed)
msd_subset_path         = os.path.join(os.getcwd(), 'data/raw/MillionSongSubset')
# path to the Million Song Helper Code
msd_code_path           = os.path.join(os.getcwd(), 'src/MSongsDB')
# path to the MSD files
msd_subset_data_path    = os.path.join(msd_subset_path, 'data')
msd_subset_addf_path    = os.path.join(msd_subset_path, 'AdditionalFiles')

# Add src directory to our path
################################

src_dir = os.path.join(os.getcwd(), 'src')
msd_src_dir = os.path.join(msd_code_path, 'PythonSrc')
if src_dir not in sys.path:
    sys.path.append(src_dir)
if msd_src_dir not in sys.path:
    sys.path.append(msd_src_dir)

## Library and src imports
###########################

import datetime
import glob
import hdf5_getters as GETTERS
import logging
import numpy as np
import pandas as pd
import sqlite3
import time
import Util
from dotenv import find_dotenv, load_dotenv

songs_with_features = list()

def export_dataset(df, filename):
    df.to_pickle(os.path.join(OUTPUT_PATH, filename))

def get_target_artist_terms():
    query = "SELECT DISTINCT term FROM artist_term WHERE artist_id = '{0}'".format(TARGET_ARTIST_ID)
    df = Util.execute_query(msd_subset_addf_path, ARTIST_TERM_DB, query)
    return set(df['term'])

def get_all_artist_terms(target_artist_terms):
    query = "SELECT * FROM artist_term"
    all_artists_terms_df = Util.execute_query(msd_subset_addf_path, ARTIST_TERM_DB, query)
    mask = all_artists_terms_df['term'].isin(target_artist_terms)
    return all_artists_terms_df.loc[mask]

def get_all_songs_df():
    query = "SELECT * FROM songs"
    songs_df = Util.execute_query(msd_subset_addf_path, TRACK_METADATA_DB, query)
    return songs_df

def get_compare_songs_df(all_artists_terms_df):
    query = "SELECT * FROM songs"
    songs_df = Util.execute_query(msd_subset_addf_path, TRACK_METADATA_DB, query)
    same_terms_artists_set = set(all_artists_terms_df['artist_id'])
    mask = songs_df['artist_id'].isin(same_terms_artists_set)
    return songs_df.loc[mask].copy(deep=True)

def find_valid_file(basedir, track_id, callback=lambda x: x, ext='.h5'):
    for root, dirs, files in os.walk(basedir):
        for file in files:
            if file.endswith(ext) and track_id in file:
                callback(os.path.join(root, file))

def get_features(filename):
    # Open the file
    h5 = GETTERS.open_h5_file_read(filename)

    # Create a dictionary entry and add it to our song list
    getter_props = (name for name in dir(GETTERS) if name.startswith('get_'))
    song_dict = dict()
    for prop in getter_props:
        key = prop.replace('get_', '')
        value = getattr(GETTERS, prop)(h5)
        song_dict[key] = value
    songs_with_features.append(song_dict)

    # Close the file!
    h5.close()

    return song_dict

def get_lyrics(artist_name, song_title):
    song = Util.Song(artist=artist_name, title=song_title)
    lyrics = song.lyricwikia()
    return lyrics

def main():
    logger = logging.getLogger(__name__)
    logger.info('Making songs_features_df data set from raw data')

    # Grab terms for the artist ID set in the config file
    # No longer using all terms from the target_artist_terms:
    #   target_artist_terms = get_target_artist_terms()
    #
    # as I was getting a lot of rock and pop that was not traditionally
    # viewed as hip hop and rap; at least the set of songs I want
    # to compare.
    #
    # Instead, I selected a handful of artist terms that are listed from
    # the susbet of Kanye West songs I will like to compare with.
    #
    target_artist_terms = [
        'alternative rap',
        'black',
        'east coast rap',
        'gangsta',
        'hip hop',
        'rap',
        'soul'
    ]

    # Grab terms for all the other artists
    all_artists_terms_df = get_all_artist_terms(target_artist_terms)

    # Get all songs from the artist_id's we know that share terms with our artist
    compare_songs_df = get_compare_songs_df(all_artists_terms_df)
    compare_songs_df = compare_songs_df['track_id'].apply(
        lambda x: find_valid_file(msd_subset_data_path, x, callback=get_features))

    # Convert list to DataFrame
    song_features_df = pd.DataFrame(songs_with_features)

    # Get song lyrics
    # song_features_df['lyrics'] = song_features_df.apply(
    #     lambda row: get_lyrics(row['artist_name'], row['title']), axis=1)

    # Export our DataFrame
    export_dataset(song_features_df, 'msd_subset_song_features_df.pkl')

    logger.info('Done!')

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()

