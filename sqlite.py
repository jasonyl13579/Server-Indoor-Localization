# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 18:06:06 2019

@author: Jason
"""

import sqlite3
import scipy.io as sio
import numpy as np
import io
import sys
from configparser import ConfigParser
import os
import pickle
#conn = sqlite3.connect('Presence_Detection.db')
database = 'PD_office_0910'
startDate = "2019-05-30"
endDate = "2019-10-10"
startTime = "01:00:00"
endTime = "18:00:00"
ini_File_name = 'app.ini'
if os.path.isfile(ini_File_name):
    print ('Find ini file.')
    cfg = ConfigParser()
    cfg.read(ini_File_name)
    database = cfg['common']['database'] 
    startDate = cfg['sqlite']['startDate']
    endDate = cfg['sqlite']['endDate']
    startTime = cfg['sqlite']['startTime']
    endTime = cfg['sqlite']['startTime']

database_path = './model/' + database + '/'
if not os.path.exists(database_path):
    os.mkdir(database_path)    
conn = sqlite3.connect(database_path + database + '.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
print ("Opened database successfully: " + database);

c = conn.cursor()

#%% create db
def create_table(conn):
    print ("Create database: " + database)
    c = conn.cursor()
    c.execute('''CREATE TABLE PD
      (CSI array NOT NULL,
      LABEL INT DEFAULT -1,
      perfomed_at TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'))
            );''')
    conn.commit()
    c.execute('''CREATE TABLE CHANGE_LABEL
      (LABEL INT DEFAULT -1,
      SCENE TEXT DEFAULT 'Teacher',
      perfomed_at TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'))
            );''')
    conn.commit()
    c.execute('''CREATE TABLE TRACK
      (LABEL INT DEFAULT -1,
      SCENE TEXT DEFAULT 'Teacher',
      perfomed_at TIMESTAMP DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME'))
            );''')
    conn.commit()
    conn.close()
    
#create_table(conn)

def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)
sqlite3.register_adapter(np.ndarray, adapt_array)
sqlite3.register_converter("array", convert_array)

#%% save_CSI as mat
def count_database():
    count = 0
    #https://stackoverflow.com/questions/27640857/best-way-to-store-python-datetime-time-in-a-sqlite3-column
    #c.execute("SELECT * FROM PD")
    c.execute("SELECT * FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' ".format(sd=startDate,ed=endDate))
    #c.execute("SELECT * FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' AND time(perfomed_at) BETWEEN '{st}' AND '{et}'".format(sd=startDate,ed=endDate,st=startTime,et=endTime))
    for row in c:
        #print (row[0])
        count = count + 1
    print("PD:" + str(count))
    c.execute("SELECT * FROM TRACK WHERE perfomed_at BETWEEN '{sd}' AND '{ed}'".format(sd=startDate,ed=endDate))
    #c.execute("SELECT * FROM TRACK WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' AND time(perfomed_at) BETWEEN '{st}' AND '{et}'".format(sd=startDate,ed=endDate,st=startTime,et=endTime))
    count = 0
    for row in c:
        #print(row[2])
        count = count + 1   
    print ("Track:" + str(count))
    '''
    c.execute("SELECT * FROM CHANGE_LABEL")
    count = 0
    for row in c:
        #print (row[2])
        count = count + 1
    print ("Change:" + str(count))
    '''
def delete_database():
    #c.execute("DELETE FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' AND time(perfomed_at) BETWEEN '{st}' AND '{et}'".format(sd=startDate,ed=endDate,st=startTime,et=endTime))
    c.execute("DELETE FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}'".format(sd=startDate,ed=endDate))
    conn.commit()
    print ("Delete database successfully.")
def save_database():
    x = []
    y = []
    count = 0
    data = {}
    #c.execute("SELECT * FROM PD")
    c.execute("SELECT * FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' ".format(sd=startDate,ed=endDate))
    #c.execute("SELECT * FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' AND time(perfomed_at) BETWEEN '{st}' AND '{et}'".format(sd=startDate,ed=endDate,st=startTime,et=endTime))
    for row in c:
        x.append(row[0])
        y.append(row[1])
        count = count + 1
    data['x_test'] = x
    data['y_test'] = y
    data['Count'] = count
    mat_path = 'data/training_data/data' + database +'.mat'    
    sio.savemat(mat_path, data)
    print ("Save to file " + mat_path)
def dump_database(db_name):
    count = 0
    c.execute("SELECT * FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' ".format(sd=startDate,ed=endDate))
    csi_database = []
    for row in c:
        x_max = np.amax(row[0], axis=0)
        x_min = np.amin(row[0], axis=0)
        #x_normolize = (row[0] - x_min)/(x_max - x_min)
        count = count + 1
        csi_database.append((row[0],row[1]))        
    with open(db_name +".db", "wb") as fp:   
        pickle.dump(csi_database, fp)
        print ("Dump:" + str(count))
        print ("Save to file " + db_name + ".db")
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create":
            create_table(conn)
        elif command == "count":
            count_database()
        elif command == "delete":
            delete_database()
        elif command == "save":
            save_database()
        elif command == "dump":
            db = "csi"
            if len(sys.argv) > 2:
                db = sys.argv[2]
            dump_database(db)
        else:
            print ("No such command.")
        conn.close()