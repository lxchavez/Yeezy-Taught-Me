"""
Thierry Bertin-Mahieux (2011) Columbia University
tb2332@columbia.edu

Code to parse the whole training set, get a summary of the features,
and save them in a KNN-ready format.

This is part of the Million Song Dataset project from
LabROSA (Columbia University) and The Echo Nest.

Copyright (c) 2011, Thierry Bertin-Mahieux, All Rights Reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import time
import glob
import copy
import tables
import sqlite3
import datetime
import multiprocessing
import numpy as np
import hdf5_getters as GETTERS


# error passing problems, useful for multiprocessing
class KeyboardInterruptError(Exception):pass


def fullpath_from_trackid(maindir,trackid):
    """ Creates proper file paths for song files """
    p = os.path.join(maindir,trackid[2])
    p = os.path.join(p,trackid[3])
    p = os.path.join(p,trackid[4])
    p = os.path.join(p,trackid+'.h5')
    return str(p)

def get_all_files(basedir,ext='.h5'):
    """
    From a root directory, go through all subdirectories
    and find all files with the given extension.
    Return all absolute paths in a list.
    """
    allfiles = []
    apply_to_all_files(basedir,func=lambda x: allfiles.append(x),ext=ext)
    return allfiles


def apply_to_all_files(basedir,func=lambda x: x,ext='.h5'):
    """
    From a root directory, go through all subdirectories
    and find all files with the given extension.
    Apply the given function func
    If no function passed, does nothing and counts file
    Return number of files
    """
    cnt = 0
    for root, dirs, files in os.walk(basedir):
        files = glob.glob(os.path.join(root,'*'+ext))
        for f in files :
            func(f)
            cnt += 1
    return cnt


def compute_features(h5):
    """
    From an open HDF5 song file, extract average and covariance of the
    timbre vectors.
    RETURN 1x90 vector or None if there is a problem
    """
    feats = GETTERS.get_segments_timbre(h5).T
    # features length
    ftlen = feats.shape[1]
    ndim = feats.shape[0]
    assert ndim==12,'WRONG DEATURE DIMENSION, transpose issue?'
    finaldim = 90
    # too small case
    if ftlen < 3:
        return None
    # avg
    avg = np.average(feats,1)
    # cov
    cov = np.cov(feats)
    covflat = []
    for k in range(12):
        covflat.extend( np.diag(cov,k) )
    covflat = np.array(covflat)
    # concatenate avg and cov
    feats = np.concatenate([avg,covflat])
    # done, reshape & return
    return feats.reshape(1,finaldim)
    
    

def process_filelist_train(filelist=None,testsongs=None,tmpfilename=None):
    """
    Main function, process all files in the list (as long as their track_id
    is not in testsongs)
    INPUT
       filelist     - a list of song files
       testsongs    - set of track ID that we should not use
       tmpfilename  - where to save our processed features
    """
    # sanity check
    for arg in locals().values():
        assert not arg is None,'process_filelist_train, missing an argument, something still None'
    if os.path.isfile(tmpfilename):
        print 'ERROR: file',tmpfilename,'already exists.'
        return
    # dimension fixed (12-dimensional timbre vector)
    ndim = 12
    finaldim = 90
    # create outputfile
    output = tables.openFile(tmpfilename, mode='a')
    group = output.createGroup("/",'data','TMP FILE FOR ARTIST RECOGNITION')
    output.createEArray(group,'feats',tables.Float64Atom(shape=()),(0,finaldim),'',
                        expectedrows=len(filelist))
    output.createEArray(group,'artist_id',tables.StringAtom(18,shape=()),(0,),'',
                        expectedrows=len(filelist))
    # iterate over files
    cnt_f = 0
    for f in filelist:
        cnt_f += 1
        # verbose
        if cnt_f % 50000 == 0:
            print 'training... checking file #',cnt_f
        # check what file/song is this
        h5 = GETTERS.open_h5_file_read(f)
        artist_id = GETTERS.get_artist_id(h5)
        track_id = GETTERS.get_track_id(h5)
        if track_id in testsongs: # just in case, but should not be necessary
            print 'Found test track_id during training? weird.',track_id
            h5.close()
            continue
        # extract features, then close file
        processed_feats = compute_features(h5)
        h5.close()
        if processed_feats is None:
            continue
        # save features to tmp file
        output.root.data.artist_id.append( np.array( [artist_id] ) )
        output.root.data.feats.append( processed_feats )
    # we're done, close output
    output.close()
    return

            
def process_filelist_train_wrapper(args):
    """ wrapper function for multiprocessor, calls process_filelist_train """
    try:
        process_filelist_train(**args)
    except KeyboardInterrupt:
        raise KeyboardInterruptError()


def process_filelist_train_main_pass(nthreads,maindir,testsongs,trainsongs=None):
    """
    Do the main walk through the data, deals with the threads,
    creates the tmpfiles.
    INPUT
      - nthreads     - number of threads to use
      - maindir      - dir of the MSD, wehre to find song files
      - testsongs    - set of songs to ignore
      - trainsongs   - list of files to use for training (faster!)
    RETURN
      - tmpfiles     - list of tmpfiles that were created
                       or None if something went wrong
    """
    # sanity checks
    assert nthreads >= 0,'Come on, give me at least one thread!'
    if not os.path.isdir(maindir):
        print 'ERROR: directory',maindir,'does not exist.'
        return None
    # get all files
    if trainsongs is None:
        allfiles = get_all_files(maindir)
    else:
        allfiles = trainsongs
    assert len(allfiles)>0,'Come on, give me at least one file in '+maindir+'!'
    if nthreads > len(allfiles):
        nthreads = len(allfiles)
        print 'more threads than files, reducing number of threads to:',nthreads
    print 'WE HAVE',len(allfiles),'POTENTIAL TRAIN FILES'
    # prepare params for each thread
    params_list = []
    default_params = {'testsongs':testsongs}
    tmpfiles_stub = 'mainpass_artistrec_tmp_output_'
    tmpfiles = map(lambda x: os.path.join(os.path.abspath('.'),tmpfiles_stub+str(x)+'.h5'),range(nthreads))
    nfiles_per_thread = int(np.ceil(len(allfiles) * 1. / nthreads))
    for k in range(nthreads):
        # params for one specific thread
        p = copy.deepcopy(default_params)
        p['tmpfilename'] = tmpfiles[k]
        p['filelist'] = allfiles[k*nfiles_per_thread:(k+1)*nfiles_per_thread]
        params_list.append(p)
    # launch, run all the jobs
    pool = multiprocessing.Pool(processes=nthreads)
    try:
        pool.map(process_filelist_train_wrapper, params_list)
        pool.close()
        pool.join()
    except KeyboardInterruptError:
        print 'MULTIPROCESSING'
        print 'stopping multiprocessing due to a keyboard interrupt'
        pool.terminate()
        pool.join()
        return None
    except Exception, e:
        print 'MULTIPROCESSING'
        print 'got exception: %r, terminating the pool' % (e,)
        pool.terminate()
        pool.join()
        return None
    # all done!
    return tmpfiles


def train(nthreads,maindir,output,testsongs,trainsongs=None):
    """
    Main function to do the training
    Do the main pass with the number of given threads.
    Then, reads the tmp files, creates the main output, delete the tmpfiles.
    INPUT
      - nthreads     - number of threads to use
      - maindir      - dir of the MSD, wehre to find song files
      - output       - main model, contains everything to perform KNN
      - testsongs    - set of songs to ignore
      - trainsongs   - list of songs to use for training (FASTER)
    RETURN
       - nothing :)
    """
    # sanity checks
    if os.path.isfile(output):
        print 'ERROR: file',output,'already exists.'
        return
    # initial time
    t1 = time.time()
    # do main pass
    tmpfiles = process_filelist_train_main_pass(nthreads,maindir,testsongs,trainsongs=trainsongs)
    if tmpfiles is None:
        print 'Something went wrong, tmpfiles are None'
        return
    # intermediate time
    t2 = time.time()
    stimelen = str(datetime.timedelta(seconds=t2-t1))
    print 'Main pass done after',stimelen; sys.stdout.flush()
    # find approximate number of rows per tmpfiles
    h5 = tables.openFile(tmpfiles[0],'r')
    nrows = h5.root.data.artist_id.shape[0] * len(tmpfiles)
    h5.close()
    # create output
    output = tables.openFile(output, mode='a')
    group = output.createGroup("/",'data','KNN MODEL FILE FOR ARTIST RECOGNITION')
    output.createEArray(group,'feats',tables.Float64Atom(shape=()),(0,90),'feats',
                        expectedrows=nrows)
    output.createEArray(group,'artist_id',tables.StringAtom(18,shape=()),(0,),'artist_id',
                        expectedrows=nrows)
    # aggregate temp files
    for tmpf in tmpfiles:
        h5 = tables.openFile(tmpf)
        output.root.data.artist_id.append( h5.root.data.artist_id[:] )
        output.root.data.feats.append( h5.root.data.feats[:] )
        h5.close()
        # delete tmp file
        os.remove(tmpf)
    # close output
    output.close()
    # final time
    t3 = time.time()
    stimelen = str(datetime.timedelta(seconds=t3-t1))
    print 'Whole training done after',stimelen
    # done
    return


def die_with_usage():
    """ HELP MENU """
    print 'process_train_set.py'
    print '   by T. Bertin-Mahieux (2011) Columbia University'
    print '      tb2332@columbia.edu'
    print 'Code to perform artist recognition on the Million Song Dataset.'
    print 'This performs the training of the KNN model.'
    print 'USAGE:'
    print '  python process_train_set.py [FLAGS] <MSD_DIR> <testsongs> <tmdb> <output>'
    print 'PARAMS:'
    print '        MSD_DIR  - main directory of the MSD dataset'
    print '      testsongs  - file containing test songs (to ignore)'
    print '           tmdb  - path to track_metadata.db'
    print '         output  - output filename (.h5 file)'
    print 'FLAGS:'
    print '    -nthreads n  - number of threads to use (default: 1)'
    print '     -onlytesta  - only train on test artists (makes problem easier!!!)'
    sys.exit(0)


if __name__ == '__main__':

    # help menu
    if len(sys.argv) < 5:
        die_with_usage()

    # flags
    nthreads = 1
    onlytesta = False
    while True:
        if sys.argv[1] == '-nthreads':
            nthreads = int(sys.argv[2])
            sys.argv.pop(1)
        elif sys.argv[1] == '-onlytesta':
            onlytesta = True
        else:
            break
        sys.argv.pop(1)

    # params
    msd_dir = sys.argv[1]
    testsongs = sys.argv[2]
    tmdb = sys.argv[3]
    output = sys.argv[4]

    # read test artists
    if not os.path.isfile(testsongs):
        print 'ERROR:',testsongs,'does not exist.'
        sys.exit(0)
    testsongs_set = set()
    f = open(testsongs,'r')
    for line in f.xreadlines():
        if line == '' or line.strip() == '':
            continue
        testsongs_set.add( line.strip().split('<SEP>')[0] )
    f.close()

    # get songlist from track_metadata.db
    # some SQL magic required
    trainsongs = None
    assert os.path.isfile(tmdb),'Database: '+tmdb+' does not exist.'
    conn = sqlite3.connect(tmdb)
    q = "CREATE TEMP TABLE testsongs (track_id TEXT)" # we'll put all test track_id here
    res = conn.execute(q)
    conn.commit()
    for tid in testsongs_set:
        q = "INSERT INTO testsongs VALUES ('"+tid+"')"
        conn.execute(q)
    conn.commit()
    q = "CREATE TEMP TABLE trainsongs (track_id TEXT)" # we'll put all train track_id here
    res = conn.execute(q)
    conn.commit()
    if not onlytesta:# every song that is not a test song (harder!)
        q = "INSERT INTO trainsongs SELECT DISTINCT track_id FROM songs"
        q += " EXCEPT SELECT track_id FROM testsongs"
        res = conn.execute(q)
    else: # only songs from artist that we test (easier!)
        q = "CREATE TEMP TABLE testartists (artist_id TEXT)" # we'll put test artists here
        res = conn.execute(q)
        conn.commit()
        q = "INSERT INTO testartists SELECT DISTINCT artist_id FROM songs"
        q += " JOIN testsongs ON testsongs.track_id=songs.track_id"
        conn.execute(q)
        conn.commit()
        # now we have test artists, get songs only from these ones
        q = "INSERT INTO trainsongs SELECT DISTINCT track_id FROM songs"
        q += " JOIN testartists ON songs.artist_id=testartists.artist_id"
        q += " EXCEPT SELECT track_id FROM testsongs"
        conn.execute(q)
    conn.commit()
    q = "SELECT track_id FROM trainsongs"
    res = conn.execute(q)
    data = res.fetchall()
    conn.close()
    print 'Found',len(data),'training files from track_metadata.db'
    trainsongs = map(lambda x: fullpath_from_trackid(msd_dir,x[0]),data)
    assert os.path.isfile(trainsongs[0]),'first training file does not exist? '+trainsongs[0]

    # settings
    print 'msd dir:',msd_dir
    print 'output:',output
    print 'testsongs:',testsongs,'('+str(len(testsongs_set))+' songs)'
    print 'trainsongs: got',len(trainsongs),'songs'
    print 'tmdb:',tmdb
    print 'nthreads:',nthreads
    print 'onlytesta:',onlytesta

    # sanity checks
    if not os.path.isdir(msd_dir):
        print 'ERROR:',msd_dir,'is not a directory.'
        sys.exit(0)
    if os.path.isfile(output):
        print 'ERROR: file',output,'already exists.'
        sys.exit(0)

    # launch training
    train(nthreads,msd_dir,output,testsongs_set,trainsongs)

    # done
    print 'DONE!'
