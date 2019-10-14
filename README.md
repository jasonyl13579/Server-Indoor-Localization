# Server for Indoor Localization
## Install and activate env
```
conda env create -f freeze.yml -n [env_name] 
source activate [env_name]
```
## Create your own app.inn
```
# Parameter common for all file
[common]
database = ED709
save_model_file_name = 0706_win100

# Parameter for server_training.py
[server]
port = 5000
count = 0

# Reserve for model use
[lstm]
class_num = 2
batch_size = 128
window_size = 100

# Parameter for sqlite.py
[sqlite]
startDate = 2019-01-30
endDate = 2019-10-10
startTime = 01:00:00
endTime = 18:00:00
```
## Using sqlite.py
```
Usage: python sqlite.py [command]
```
command:
* create -- create database {database}
* count -- count csi between time interval {startDate} and {endDate} in database {database}
* delete -- delete csi between time interval {startDate} and {endDate} in database {database}
* save -- save csi between time interval {startDate} and {endDate} in database {database} into .mat file
* dump [filename] -- save csi between time interval {startDate} and {endDate} in database {database} into {filename}.db file

## Using server.py
```
Usage: python server.py [optional commands(-hsldp)]
 [-h] help
 [-s] Enable prediction
 [-l] Enable global label
 [-d] Debug mode (Do not save data into database)
 [-p <port>] Port
```
