import requests
import time
import datetime
import os
import threading
import sys
import configparser
import multiprocessing
import streamlink
import gc
import collections
import subprocess
import queue

if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

mainDir = sys.path[0]
Config = configparser.ConfigParser()
setting = {}

recording = []
UserAgent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Mobile Safari/537.36"

hilos = []

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def readConfig():
    global setting

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
    
class Modelo(threading.Thread):
    def __init__(self, modelo):
        threading.Thread.__init__(self)
        self.modelo = modelo.lower()
        self._stopevent = threading.Event()
        self.file = None
        self.online = None
        self.lock = threading.Lock()
        
    def run(self):
        global recording, hilos
        isOnline = self.isOnline()
        if isOnline == False:
            self.online = False
        else:
            self.file = os.path.join(setting['save_directory'], self.modelo, "{st}_{model}.mp4".format(path=setting['save_directory'], model=self.modelo, st=datetime.datetime.fromtimestamp(time.time()).strftime("%Y.%m.%d_%H.%M.%S")))
            self.online = True
            try:
                session = streamlink.Streamlink()
                session.set_option('http-headers', "referer=https://www.cam4.com/{}".format(self.modelo))
                streams = session.streams("hlsvariant://https://{}/amlst:{}_aac/playlist.m3u8?referer=www.cam4.com&timestamp={}".format(isOnline['videoAppUrl'], isOnline['videoPlayUrl'], str(int(time.time() * 1000))))
                stream = streams["best"]
                fd = stream.open()
                if not any(obj.modelo == self.modelo for obj in recording):
                    os.makedirs(os.path.join(setting['save_directory'], self.modelo), exist_ok=True)
                    with open(self.file, 'wb') as f:
                        self.lock.acquire()
                        try:
                            recording.append(self)
                            for hilo in hilos:
                                if hilo.modelo == self.modelo:
                                    hilos.remove(hilo)
                        finally:
                            self.lock.release()
                        while not (self._stopevent.isSet() or os.fstat(f.fileno()).st_nlink == 0):
                            try:
                                data = fd.read(1024)
                                f.write(data)
                            except:
                                self.stop()
                    if setting['postProcessingCommand']:
                            processingQueue.put({'model': model, 'path': self.file})
            except Exception:
                pass
            finally:
                self.exceptionHandler()
                    
    def exceptionHandler(self):
        self.stop()
        self.online = False
        self.lock.acquire()
        try:
            for hilo in recording:
                if hilo.modelo == self.modelo:
                    recording.remove(hilo)
        finally:
            self.lock.release()
            
    def isOnline(self):
        try:
            resp = requests.get('https://www.cam4.com/' + self.modelo, headers={'user-agent':'UserAgent'}).text.splitlines()
            videoPlayUrl = ""
            videoAppUrl = ""
            for line in resp:
                if "videoPlayUrl" in line:
                    for part in line.split("&"):
                        if "videoPlayUrl" in part and videoPlayUrl == "":
                            videoPlayUrl = part[13:]
                        elif "videoAppUrl" in part and videoAppUrl == "":
                            videoAppUrl = part.split("//")[1]
            if videoAppUrl == "" and videoPlayUrl == "":
                return False
            else:
                return {'videoPlayUrl': videoPlayUrl, 'videoAppUrl': videoAppUrl}
        except Exception:
            return False

    def stop(self):
        self._stopevent.set()

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
        subprocess.call(setting['postProcessingCommand'].split() + [path, filename, directory, model,  file, 'cam4'])

class CleaningThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.interval = 0
        self.lock = threading.Lock()
        
    def run(self):
        global hilos, recording
        while True:
            self.lock.acquire()
            try:
                for hilo in hilos:
                    if hilo.is_alive() == False and hilo.online == False:
                        hilo.stop()
                        hilo.join()
                        hilos.remove(hilo)
            finally:
                self.lock.release()
            for i in range(10, 0, -1):
                self.interval = i
                time.sleep(1)
            gc.collect()

class AddModelsThread(threading.Thread):
    def __init__(self, wanted):
        threading.Thread.__init__(self)
        self.wanted = wanted
        self.lock = threading.Lock()

    def run(self):
        global hilos, recording
        self.lock.acquire()
        try:
            for model in self.wanted:
                if not (any(obj.modelo == model for obj in hilos) or any(obj.modelo == model for obj in recording)):
                    thread = Modelo(model)
                    thread.start()
                    hilos.append(thread)
        finally:
            self.lock.release()
    
if __name__ == '__main__':
    readConfig()
    if setting['postProcessingCommand']:
        processingQueue = queue.Queue()
        postprocessingWorkers = []
        for i in range(0, setting['postProcessingThreads']):
            t = threading.Thread(target=postProcess)
            postprocessingWorkers.append(t)
            t.start()

    cleaningThread = CleaningThread()
    cleaningThread.start()
    while True:
        try:
            readConfig()
            wanted = []
            i = 1
            with open(setting['wishlist']) as f:
                for model in f:
                    models = model.split()
                    for theModel in models:
                        wanted.append(theModel.lower())
                    del models
            addModelsThread = AddModelsThread(wanted)
            addModelsThread.start()
            repeatedModels = [key for key, value in collections.Counter(wanted).items() if value > 1]

            for hilo in recording:
                if hilo.modelo not in wanted:
                    hilo.stop()

            for i in range(setting['interval'], 0, -1):
                cls()
                if len(repeatedModels): print("The following models are more than once in wanted:".format(i),"['" + ", ".join(modelo for modelo in repeatedModels) + "']")
                print("{:02d} alive Threads (1 Thread per non-recording model), cleaning dead/not-online Threads in {:02d} seconds, {:02d} models in wanted".format(len(hilos), cleaningThread.interval, len(wanted)))
                print("Online Threads (models): {:02d}".format(len(recording)))
                print("The following models are being recorded:")
                for hiloModelo in recording: print("  Model: {}  -->  File: {}".format(hiloModelo.modelo, os.path.basename(hiloModelo.file)))
                print("Next check in {:02d} seconds".format(i))
                time.sleep(1)
            addModelsThread.join()
            del wanted, i, repeatedModels, addModelsThread
            gc.collect()
        except:
            break
