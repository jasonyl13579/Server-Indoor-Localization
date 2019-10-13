# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 17:31:27 2019

@author: User
"""

# build map
import sqlite3
from configparser import ConfigParser
import os
import pickle
import io
import numpy as np


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


c = conn.cursor()
count = 0
c.execute("SELECT * FROM PD WHERE perfomed_at BETWEEN '{sd}' AND '{ed}' ".format(sd=startDate,ed=endDate))
csi_database = []
temp = 0
for row in c:
    x_max = np.amax(row[0], axis=0)
    x_min = np.amin(row[0], axis=0)
    x_normolize = (row[0] - x_min)/(x_max - x_min)
    count = count + 1
    csi_database.append((x_normolize,row[1]))
    
print (count)
with open("example_normolize.db", "wb") as fp:   
    pickle.dump(csi_database, fp)
