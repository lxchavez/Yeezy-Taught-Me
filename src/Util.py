import os
import datetime
import pandas as pd
import sqlite3
import urllib
from urlparse import urlparse
import lxml.html

def execute_query(db_path, db_name, query):
    ### Returns a DataFrame containing the query results
        
    # Read sqlite query results into a pandas DataFrame
    con = sqlite3.connect(os.path.join(db_path, db_name))
    df = pd.read_sql_query(query, con)
    con.close()
                            
    return df   

# the following function simply gives us a nice string for
# a time lag in seconds
def strtimedelta(starttime, stoptime):
    return datetime.timedelta(seconds=stoptime-starttime)

# Sebastian Raschka, 2014
# 
# Script to download lyrics from http://lyrics.wikia.com/

class Song(object):
    def __init__(self, artist, title):
        self.artist = self.__format_str(artist)
        self.title = self.__format_str(title)
        self.url = None
        self.lyric = None
        
    def __format_str(self, s):
        # remove paranthesis and contents
        s = s.strip()
        try:
            # strip accent
            s = ''.join(c for c in unicodedata.normalize('NFD', s)
                         if unicodedata.category(c) != 'Mn')
        except:
            pass
        s = s.title()
        return s
        
    def __quote(self, s):
#          return urlparse.quote(s.replace(' ', '_'))
        return s.replace(' ', '_')

    def __make_url(self):
        artist = self.__quote(self.artist)
        title = self.__quote(self.title)
        artist_title = '%s:%s' %(artist, title)
        url = 'http://lyrics.wikia.com/' + artist_title
        self.url = url
        
    def update(self, artist=None, title=None):
        if artist:
            self.artist = self.__format_str(artist)
        if title:
            self.title = self.__format_str(title)
        
    def lyricwikia(self):
        self.__make_url()
        try:
            doc = lxml.html.parse(self.url)
            lyricbox = doc.getroot().cssselect('.lyricbox')[0]
        except (IOError, IndexError) as e:
            self.lyric = ''
            return self.lyric
        lyrics = []

        for node in lyricbox:
            if node.tag == 'br':
                lyrics.append('\n')
            if node.tail is not None:
                lyrics.append(node.tail)
        self.lyric =  "".join(lyrics).strip()    
        return self.lyric

class Song(object):
    def __init__(self, artist, title):
        self.artist = self.__format_str(artist)
        self.title = self.__format_str(title)
        self.url = None
        self.lyric = None
        
    def __format_str(self, s):
        # remove paranthesis and contents
        s = s.strip()
        try:
            # strip accent
            s = ''.join(c for c in unicodedata.normalize('NFD', s)
                         if unicodedata.category(c) != 'Mn')
        except:
            pass
        s = s.title()
        return s
        
    def __quote(self, s):
#          return urlparse.quote(s.replace(' ', '_'))
        return s.replace(' ', '_')

    def __make_url(self):
        artist = self.__quote(self.artist)
        title = self.__quote(self.title)
        artist_title = '%s:%s' %(artist, title)
        url = 'http://lyrics.wikia.com/' + artist_title
        self.url = url
        
    def update(self, artist=None, title=None):
        if artist:
            self.artist = self.__format_str(artist)
        if title:
            self.title = self.__format_str(title)
        
    def lyricwikia(self):
        self.__make_url()
        try:
            doc = lxml.html.parse(self.url)
            lyricbox = doc.getroot().cssselect('.lyricbox')[0]
        except (IOError, IndexError) as e:
            self.lyric = ''
            return self.lyric
        lyrics = []

        for node in lyricbox:
            if node.tag == 'br':
                lyrics.append('\n')
            if node.tail is not None:
                lyrics.append(node.tail)
        self.lyric =  "".join(lyrics).strip()    
        return self.lyric
