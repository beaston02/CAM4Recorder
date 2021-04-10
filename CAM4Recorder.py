import requests, time, datetime, os, threading, sys, configparser
import uuid
import glob
from streamlink import Streamlink

if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

from subprocess import call
from queue import Queue

mainDir = sys.path[0]
Config = configparser.ConfigParser()
setting = {}

recording = []
UserAgent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Mobile Safari/537.36"

notonline = []

def readConfig():
    global setting
    global filter

    Config.read(mainDir + "/config.conf")
    setting = {
        'save_directory': Config.get('paths', 'save_directory'),
        'wishlist': Config.get('paths', 'wishlist'),
        'interval': int(Config.get('settings', 'checkInterval')),
        'postProcessingCommand': Config.get('settings', 'postProcessingCommand'),
        }
    try:
        setting['postProcessingThreads'] = int(Config.get('settings', 'postProcessingThreads'))
    except ValueError:
        if setting['postProcessingCommand'] and not setting['postProcessingThreads']:
            setting['postProcessingThreads'] = 1
    
    if not os.path.exists("{path}".format(path=setting['save_directory'])):
        os.makedirs("{path}".format(path=setting['save_directory']))

def startRecording(model):
    global notonline
    global recording 

    thread = threading.currentThread()

    try:
        model = model.lower()
        resp = requests.get('https://www.cam4.com/' + model, headers={'user-agent': UserAgent}).text.splitlines()
       
        hlsUrl = ""
        for line in resp:
            if "hlsUrl:" in line:
                s = line[line.index("hlsUrl"):]
                l = s.index("'")
                p = s[l+1:].index("'")
                hlsUrl = s[l+1:p+9]
           
        if hlsUrl == "":
            notonline.append(model)
            return

        if model in notonline:
            notonline.remove(model)

        session = Streamlink()
        session.set_option('http-headers', "referer=https://www.cam4.com/{}".format(model))
        
        streams = session.streams("{}?referer=www.cam4.com&timestamp={}"
        .format(hlsUrl, str(int(time.time() * 1000))))
        
        stream = streams["best"]
        fd = stream.open()
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime("%Y.%m.%d_%H.%M.%S")
        _uuid = uuid.uuid4()

        path = os.path.join(setting['save_directory'], model) + '/*'
        listFiles = glob.glob(path)

        if len(listFiles) == 0:
            file = os.path.join(setting['save_directory'], model, "{st}_{model}_{_uuid}.mp4".format(path=setting['save_directory'], model=model,
                                                            st=st, _uuid=_uuid))
        else:
            file = max(listFiles, key=os.path.getmtime)
            timeLatest = os.path.getmtime(file)
            if timeLatest is None or time.time() - timeLatest > 300:
                file = os.path.join(setting['save_directory'], model, "{st}_{model}_{_uuid}.mp4".format(path=setting['save_directory'], model=model,
                                                                st=st, _uuid=_uuid))
        
        os.makedirs(os.path.join(setting['save_directory'], model), exist_ok=True)
        with open(file, 'ab') as f:
            recording.append(model)
            while getattr(thread, "do_run", True):
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    break
        if setting['postProcessingCommand']:
            processingQueue.put({'model': model, 'path': file})
    except Exception as e:
        pass
    finally:
        if model not in notonline:
	        notonline.append(model)
        if model in recording:
            recording.remove(model)

def postProcess():
    while True:
        while processingQueue.empty():
            time.sleep(1)
        parameters = processingQueue.get()
        model = parameters['model']
        path = parameters['path']
        filename = os.path.split(path)[-1]
        directory = os.path.dirname(path)
        file = os.path.splitext(filename)[0]
        call(setting['postProcessingCommand'].split() + [path, filename, directory, model,  file, 'cam4'])

def getThreadByName(name):
    threads = threading.enumerate()
    for thread in threads:
        if thread.name == name:
            return thread

if __name__ == '__main__':
    readConfig()
    if setting['postProcessingCommand']:
        processingQueue = Queue()
        postprocessingWorkers = []
        for i in range(0, setting['postProcessingThreads']):
            t = threading.Thread(target=postProcess)
            postprocessingWorkers.append(t)
            t.start()

    while True:
        try: 
            readConfig()
            wanted = []
            i = 1
            notonline = []
            
            with open(setting['wishlist']) as f:
                for model in f:
                    models = model.split()
                    for theModel in models:
                        if theModel not in wanted:
                            wanted.append(theModel.lower())

            for model in wanted:
                if model not in recording:
                    thread = threading.Thread(name=model, target=startRecording, args=(model,))
                    thread.do_run = True
                    thread.start()
            
            for model in recording:
                if model not in wanted:
                    thread = getThreadByName(model)
                    thread.do_run = False
                    thread.join()

            for i in range(setting['interval'], 0, -1):
                print("{} not online Next check in {} seconds".format(notonline, i))
                print("the following models are being recorded: {}".format(recording))
                time.sleep(1)
        except Exception as e:
            print(e, flush=True)
            break       