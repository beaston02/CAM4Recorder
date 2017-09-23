# CAM4Recorder

This is script to automate the recording of public webcam shows from cam4. 


## Requirements:

A machine running a recent Linux distro, I have tested this on Debian (7+8) and Mac OS X (10.10.4)

Python 3.5 or newer https://www.python.org/downloads/release/python-362/

## installing and Cloning with the required modules:

to install the required modules, run: (For Debain/Ubuntu)
```
sudo apt-install update && sudo apt install upgrade
sudo apt-install python3-pip && sudo pip3 install livestreamer && sudo apt-get install git clone
cd /home/yourusername
git clone https://github.com/beaston02/CAM4Recorder
cd CAM4Recorder
(Optional) sudo apt-install gitclone && sudo apt-install ffmpeg
```

to install the required modules, run: (For CentOS/Red Hat/Fedora)
```
yum update
yum upgrade
yum python3-pip
pip3 install livestreamer
yum install git clone
cd /home/yourusername
git clone https://github.com/beaston02/CAM4Recorder
cd CAM4Recorder
(Optional) yum install ffmpeg
```

to install required modules, run: (For Arch Linux, Antergos, Manjaro, etc.)
```
pacman -Syuu
pacman -S python-pip git
pip install livestreamer
cd /home/yourusername
git clone https://github.com/beaston02/CAM4Recorder
cd CAM4Recorder
(Optional maybe Feature releases?) sudo apt-install ffmpeg

```
## Config and Run

Configure the settings in the config file. Set the path to the wishlist and save_directory. You can adjust the check interval, or leave it at 20 seconds

Add models to the "wanted.txt" file (only one model per line). The model should match the models name in their chatrooms URL (https://www.cam4.com/{modelname}). 

you can create your own post processing script to run on the completed files and set the command and number of threads (the number of files which could be processed at one time) in the config file. The arguments that are passed to the script are:
1 = full file path (ie: /Users/Joe/cam4/hannah/2017.07.26_19.34.47_hannah.mp4)
2 = filename (ie : 2017.07.26_19.34.47_hannah.mp4)
3 = directory (ie : /Users/Joe/cam4/hannah/)
4 = models name (ie: hannah)
5 = filename without the extension (ie: 2017.07.26_19.34.47_hannah)
6 = 'cam4' - thats it, just 'cam4' to identify the site
