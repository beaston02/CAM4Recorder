# CAM4Recorder

This is script to automate the recording of public webcam shows from cam4. 


## Requirements

I have only tested this on debian(7+8) and Mac OS X (10.10.4), but it should run on other OSs

Requires python3.5 or newer. You can grab python3.5.2 from https://www.python.org/downloads/release/python-352/

to install required modules, run:
```
python3.5 -m pip install livesteramer
```


Edit lines 6 and 8 to set the path for the directory to save the videos to, and to set the location of the "wanted.txt" file.

Add models to the "wanted.txt" file (only one model per line). The model should match the models name in their chatrooms URL (https://www.cam4.com/{modelname}). 
