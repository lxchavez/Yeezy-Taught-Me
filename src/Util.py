import os
import datetime
import pandas as pd
import sqlite3

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
