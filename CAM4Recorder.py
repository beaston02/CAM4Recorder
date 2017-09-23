import requests, time, datetime, os, threading, sys, configparser
from livestreamer import Livestreamer
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
from subprocess import call
from queue import Queue

mainDir = sys.path[0]
Config = configparser.ConfigParser()
setting = {}
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
recording = []
UserAgent = "Mozilla/5.0 (Linux; Android 7.1.2; Nexus 6P Build/N2G48C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.116 Mobile Safari/537.36"
offline = False

def getOnlineModels(page):
    i = 1
    while i < 5:
        try:
            sys.stdout.write("\033[K")
            print("{} model(s) are being recorded. Checking for models to record (page {})".format(len(recording), page))
            sys.stdout.write("\033[K")
            print("the following models are being recorded: {}".format(recording), end="\r")
            result = requests.get("https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&page={}".format(page)).json()
            return result
        except:
            i = i + 1
            sys.stdout.write("\033[F")

def startRecording(model):
    try:
        model = model.lower()
        resp = requests.get('https://www.cam4.com/' + model, headers={'user-agent':'UserAgent'}).text.splitlines()
        videoPlayUrl = ""
        videoAppUrl = ""
        for line in resp:
            if "videoPlayUrl" in line:
                for part in line.split("&"):
                    if "videoPlayUrl" in part and videoPlayUrl == "":
                        videoPlayUrl = part[13:]
                    elif "videoAppUrl" in part and videoAppUrl == "":
                        videoAppUrl = part.split("//")[1]
        session = Livestreamer()
        session.set_option('http-headers', "referer=https://www.cam4.com/{}".format(model))
        streams = session.streams("hlsvariant://https://{}/amlst:{}_aac/playlist.m3u8?referer=www.cam4.com&timestamp={}"
          .format(videoAppUrl, videoPlayUrl, str(int(time.time() * 1000))))
        stream = streams["best"]
        fd = stream.open()
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime("%Y.%m.%d_%H.%M.%S")
        file = os.path.join(setting['save_directory'], model, "{st}_{model}.mp4".format(path=setting['save_directory'], model=model,
                                                            st=st))
        os.makedirs(os.path.join(setting['save_directory'], model), exist_ok=True)
        with open(file, 'wb') as f:
            recording.append(model)
            while True:
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    break
        if setting['postProcessingCommand']:
            processingQueue.put({'model': model, 'path': file})
    finally:
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
        readConfig()
        wanted = []
        i = 1
        with open(setting['wishlist']) as f:
            for model in f:
                models = model.split()
                for theModel in models:
                    wanted.append(theModel.lower())
        while not offline:
            results = getOnlineModels(i)
            if len(results['users']) >= 1:
                for model in results['users']:
                     if model['username'].lower() in wanted and model['username'].lower() not in recording:
                         thread = threading.Thread(target=startRecording, args=(model['username'].lower(),))
                         thread.start()
            else:
                offline = True
            i = i + 1
            sys.stdout.write("\033[F")
        offline = False
        for i in range(setting['interval'], 0, -1):
            sys.stdout.write("\033[K")
            print("{} model(s) are being recorded. Next check in {} seconds".format(len(recording), i))
            sys.stdout.write("\033[K")
            print("the following models are being recorded: {}".format(recording), end="\r")
            time.sleep(1)
            sys.stdout.write("\033[F")
