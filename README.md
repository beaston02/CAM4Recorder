# CAM4Recorder

This is script to automate the recording of public webcam shows from cam4. 


## Requirements

I have only tested this on debian(7+8) and Mac OS X (10.10.4), but it should run on other OSs

Requires python3.5 or newer. You can grab python3.5.2 from https://www.python.org/downloads/release/python-352/

to install required modules, run:
```
python3.5 -m pip install livestreamer
```


## setup

Configure the settings in the config file. Set the path to the wishlist and save_directory. You can adjust the check interval, or leave it at 20 seconds

Add models to the "wanted.txt" file (only one model per line). The model should match the models name in their chatrooms URL (https://www.cam4.com/{modelname}). 

you can create your own post processing script to run on the completed files and set the command and number of threads (the number of files which could be processed at one time) in the config file. The arguments that are passed to the script are:
1 = full file path (ie: /Users/Joe/cam4/hannah/2017.07.26_19.34.47_hannah.mp4)
2 = filename (ie : 2017.07.26_19.34.47_hannah.mp4)
3 = directory (ie : /Users/Joe/cam4/hannah/)
4 = models name (ie: hannah)
5 = filename without the extension (ie: 2017.07.26_19.34.47_hannah)
6 = 'cam4' - thats it, just 'cam4' to identify the site
