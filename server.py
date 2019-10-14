# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 13:17:22 2018

@author: JasonHuang
"""
from flask import Flask, send_file, request, abort, g
import sys, getopt
from collections import Counter
import numpy as np
import sqlite3
import io
from datetime import datetime

import pickle
from configparser import ConfigParser
import os
import math
#from flask_script import Manager

app = Flask(__name__)
#manager = Manager(app)

status = []
global_label = 0
for i in range(0,20):
    status.append(1)
#%% default parameter

#Online
save_model_file_name = '0706_win100_PD_office'
#Offline
database = 'PD_office_0910'
database_path = './model/' + database + '/'
enable_prediction = False
enable_global_label = False
debug = False
port = 5000
count = 0
rps = [ \
(15,15), (15,45), (15,75), (15,105), (15,135), (15,165), (15,195),\
(45,15), (45,45), (45,75), (45,105), (45,135), (45,165), (45,195),\
(75,15), (75,45), (75,75), (75,105), (75,135), (75,165), (75,195),\
(105,15), (105,45), (105,75), (105,105), (105,135), (105,165), (105,195),\
]
with open("database_normolize.db", "rb") as fp:   # Unpickling
    csi_db = pickle.load(fp)

correlation = np.zeros((len(csi_db), 4))
        
def readini():
    ini_File_name = 'app.ini'
    if os.path.isfile(ini_File_name):
        global database, port, save_model_file_name, database_path
        print ('Find ini file.')
        cfg = ConfigParser()
        cfg.read(ini_File_name)
        database = cfg['common']['database']
        save_model_file_name = cfg['common']['save_model_file_name']
        port = cfg['server'].getint('port')
        database_path = './model/' + database + '/'
#%% user-defined model
def get_location(test):
    for i, csi_pair in enumerate(csi_db):
        for j in range(4):    
            corr = np.corrcoef(test[:,j],csi_pair[0][:,j])
            correlation[i, j] = corr[0,1]
    index = math.floor(np.argmax(correlation)/4)
    location = rps[csi_db[index][1]-1]
    print("Location at:" + str(location) + ", index:" + str(csi_db[index][1]), file=sys.stderr)
    return location
#%% sqlite init
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(database_path + database + '.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
        # Enable foreign key check
        print ("Opened database successfully");
        db.execute("PRAGMA foreign_keys = ON")
    return db
#%%sqlite array type
        
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
#%% server
#app = Flask(__name__)

picture_path = "templates/seat/"
buckets = []
multi = []
x_predict = []
for i in range(0,100):
    buckets.append(0)
def func():
    print ("HIHI",file = sys.stderr)    
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/graphic', methods=['GET'])
def get_graphic():
    filename = case("graphic")
    return send_file(filename, mimetype='image/gif')
@app.route('/', methods=['GET'])
@app.route('/text', methods=['GET'])
def get_text():
    return case("text")
    #return Response(render_template('index.html'),mimetype='text/html')
def case(TYPE):
    value = Counter(status).most_common(1)[0][0]
    if TYPE == "graphic":
            return (picture_path + str(value) + ".jpg") 
    if TYPE == "text":
                
        return "case" + str(value)
@app.route('/', methods=['POST'])
def post_data_from_router():
    global count
    global x
    if not request.json or not 'row'in request.json:
        abort(400)
    if not 'column'in request.json or not 'csi_array'in request.json:
        abort(400)
    row = request.json['row']
    column = request.json['column']
    csi_array = request.json['csi_array']
    
    #[antenna 00 antenna 01 antenna 10 antenna 11]
    np_x = np.array(csi_array)
    np_x = np.sqrt(np_x)
    np_x = np.reshape(np_x, (row, column));
    np_x = np.transpose(np_x)
   # app.logger.debug("Array:%s\n", np_x)
    x_max = np.amax(np_x, axis=0)
    x_min = np.amin(np_x, axis=0)
    x_normolize = (np_x - x_min)/(x_max - x_min)
    #x_normolize = np_x
   # app.logger.debug("Array:%s\n", x_normolize)

    if 'type' in request.json and 'label' in request.json:
        count = count + 1
        if not enable_global_label and request.json['type'] is 'l':
            multi.append([x_normolize, request.json['label'],datetime.now()])
            app.logger.debug("Count:%d, Append from router:%s\n", count, request.json['label'])
        else:
            multi.append([x_normolize, global_label ,datetime.now()])
            app.logger.debug("Count:%d, Append from global:%s\n", count, global_label)  
    if not debug:
        if count % 100 == 0:
            db = get_db()
            cursor = db.cursor()
            cursor.executemany("INSERT INTO PD (CSI,LABEL,perfomed_at)\
                               VALUES(?,?,?)", (multi))
            db.commit()
            multi.clear()    
            app.logger.debug("Insert data\n")
    if enable_prediction:
        get_location(x_normolize)

    ## Draw CSI picture
    '''
    for i in range(1,5):
        plt.subplot(2,2,i)
        plt.plot(x_normolize[i-1])
    plt.savefig('template/csi_plot')
    plt.gcf().clear()
    '''    
    
    #print("Response\n", file=sys.stderr);
    return 'POST_OK'
@app.route('/change_label', methods=['POST'])
def change_label_post():
    global global_label
    #app.logger.debug(request.json)
    if 'type' in request.json and 'label' in request.json and request.json['type'] is 2 and not debug: # type == 2 change label
        global_label = request.json['label']
        print("Change Label:" + str(global_label), file=sys.stderr)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO CHANGE_LABEL (LABEL,SCENE,perfomed_at)\
          VALUES(?,?,?)", (global_label,request.json['scene'],datetime.now()))
        db.commit()
        if 'scene' in request.json:
            scene = request.json['scene']
            #print("Scene:" + scene, file=sys.stderr)
    return 'OK'
@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    #print ("Close server.", file=sys.stderr)

if __name__ == '__main__':
    global modelName 
    modelName = "LSTM"
    readini()
    try:
        opts, args = getopt.getopt(sys.argv[1:],"shldp:o",["port"])
    except getopt.GetoptError:
        print ('Usage: server.py\n [-s] Enable prediction\n [-l] Enable global label\n [-d] Debug mode (Do not save data into database)\n [-p <port>] Port\n')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('Usage: server.py\n [-s] Enable prediction\n [-l] Enable global label\n [-d] Debug mode (Do not save data into database)\n [-p <port>] Port\n')
            sys.exit()
        if opt == '-s':
            enable_prediction = True
            #load_lstm_model()
            print ("Enable_prediction.")
        if opt == '-l':
            enable_global_label = True
            print ("Enable global label.")
        if opt == '-d':
            debug = True
            print ("Debug mode. (Do not save data into database)")    
        if opt == '-p':
            port = arg
        if opt == '-o':
            modelName = "OUTLIER"
            print ("Model = outlier")  
    if enable_prediction is True:
        print ("")
        #load_model_by_name(modelName)
    
    print ("Using database: " + database + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)