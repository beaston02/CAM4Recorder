import urllib.request, json, time, datetime, os, threading, sys
from livestreamer import Livestreamer


#specify path to save to ie "/Users/Joe/cam4"
save_directory = "/Users/Joe/cam4"
#specify the path to the wishlist file ie "/Users/Joe/cam4/wanted.txt"
wishlist = "/Users/Joe/cam4/wanted.txt"
online = []
if not os.path.exists("{path}".format(path=save_directory)):
    os.makedirs("{path}".format(path=save_directory))
recording = []
UserAgent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Mobile Safari/537.36"
offline = False

def getOnlineModels(page):
    i = 1
    while i < 5:
        try:
            sys.stdout.write("\033[K")
            print("{} model(s) are being recorded. Checking for models to record (page {})".format(len(recording), page))
            sys.stdout.write("\033[K")
            print("the following models are being recorded: {}".format(recording), end="\r")
            result = urllib.request.urlopen("https://www.cam4.com/directoryCams?directoryJson=true&online=true&url=true&page={}".format(page))
            result = result.read()
            results = json.loads(result.decode())
            return results
        except:
            i = i + 1
            sys.stdout.write("\033[F")

def startRecording(model):
    try:
        model = model.lower()
        req = urllib.request.Request('https://www.cam4.com/' + model)
        req.add_header('UserAgent', UserAgent)
        resp = urllib.request.urlopen(req)
        resp = resp.read().decode().splitlines()
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
        if not os.path.exists("{path}/{model}".format(path=save_directory, model=model)):
            os.makedirs("{path}/{model}".format(path=save_directory, model=model))
        with open("{path}/{model}/{st}_{model}.mp4".format(path=save_directory, model=model,
                                                           st=st), 'wb') as f:
            recording.append(model)
            while True:
                try:
                    data = fd.read(1024)
                    f.write(data)
                except:
                    recording.remove(model)

        if model in recording:
            recording.remove(model)
    except:
        if model in recording:
            recording.remove(model)


if __name__ == '__main__':
    while True:
        wanted = []
        i = 1
        with open(wishlist) as f:
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
        for i in range(20, 0, -1):
            sys.stdout.write("\033[K")
            print("{} model(s) are being recorded. Next check in {} seconds".format(len(recording), i))
            sys.stdout.write("\033[K")
            print("the following models are being recorded: {}".format(recording), end="\r")
            time.sleep(1)
            sys.stdout.write("\033[F")
