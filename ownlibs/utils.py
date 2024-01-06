import json
import requests
import time
import random
import speech_recognition as sr
import librosa
import soundfile as sf
import os
import tensorflow as tf
import pickle
from thefuzz import fuzz


from pyarabic import araby
from datetime import datetime

def list_surah():
    """
    \n return dict of surah data 0-113
    """
    surahs = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah").text)
    return surahs["data"]

def req_surah(surah_number=1):
    """ return surah complete of surah dict, param 1-114 """
    surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{surah_number}").text)
    return surah

def get_surah_by_ayahnquran(ayahnquran=0):
    """return int surah number from 0-113 by its ayahnquran"""
    try:
        with open("n_ayahinquran.json", "r") as f:
            inf = json.load(f)
    except:
        with open("ownlibs/n_ayahinquran.json", "r") as f:
            inf = json.load(f)

    if ayahnquran < 7:
        surah_number = 0
    elif ayahnquran >= 6230:
        surah_number = 113
    else:
        for i in range(1, len(inf)):
            # print(f"\titer {i}")
            if inf[f"{(i-1)}"] < ayahnquran and ayahnquran < inf[f"{(i+1)}"]:
                surah_number = list(inf.keys())[i]
                # print(f'{inf[f"{(i-1)}"]}, {inf[f"{(i+1)}"]}, {list(inf.keys())[i]}')
                break
    
    return int(surah_number)


def get_ayahnquran(surahn, ayahn):
    """return ayah number in quran from 0-6235
    \n param surah from 1-114, ayah from 0-n
    """
    try:
        with open("n_ayahinquran.json", "r") as f:
            info = json.load(f)
    except:
        with open("ownlibs/n_ayahinquran.json", "r") as f:
            info = json.load(f)
    
    result = info[f"{int(surahn)-1}"] + int(ayahn)

    return result

def get_ayahnsurah(surahn, ayahnquran):
    """
    return int of ayahn 1-n
    \n param surahn 0-113, if none auto find, ayahnquran 0-6325
    """

    with open("ownlibs\\n_ayahinsurah.json", "r") as f:
        inf = json.load(f)
    
    temp = 0

    if ayahnquran <0:
        res = 0
    elif ayahnquran >= 6236:
        res = 5
    elif surahn>0:
        for i in range(surahn):
            temp += inf[f"{i}"] 
        res = ayahnquran-temp
    else:
        res = ayahnquran
    return res+1


def get_total_ayahnsurah(surahn=1):
    """
    \n return int of total ayah in surah
    \n param surahn 1-114
    """
    with open("ownlibs\\n_ayahinsurah.json", "r") as f:
        inf = json.load(f)

    return int(inf[f"{surahn-1}"])

def disp_surahn_ayahn(ayahnquran=0):
    """
    \n return surah surah name and ayahnsurah 1-n
    """
    surahn = get_surah_by_ayahnquran(ayahnquran)
    ayahn = get_ayahnsurah(surahn, ayahnquran)
    surahn = list_surah()[surahn]['name']
    return surahn, ayahn

def req_juz_stats(juz=0, length_only=False):
    """ return list of ayahnquran, len ayah
    juz 0-29
    """
    try:
        with open("inf_juz.json", "r") as f:
            inf = json.load(f)
        inf = inf[f"{juz}"]
    except:
        with open("ownlibs/inf_juz.json", "r") as f:
            inf = json.load(f)
        inf = inf[f"{juz}"]

    n_ayah = 0
    ls_ayahnquran = []

    n_ayah = get_ayahnquran(inf["surahs"]+1, inf["ayahs"][0])
    
    if inf["surahe"] - inf["surahs"] <=0 :
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1}").text)
        for i in range(inf["ayahs"][0], inf["ayahs"][1]):
            ls_ayahnquran.append(n_ayah)
            n_ayah += 1 

    elif 0 < inf["surahe"] - inf["surahs"] < 2:
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1}").text)
        for i in range(inf["ayahs"][0], inf["ayahs"][1]):
            ls_ayahnquran.append(n_ayah)
            n_ayah += 1 
        
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahe']+1}").text)
        for i in range(inf["ayahe"][0], inf["ayahe"][1]):
            ls_ayahnquran.append(n_ayah)
            n_ayah += 1 

    else:
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1}").text)
        for i in range(inf["ayahs"][0], inf["ayahs"][1]):
            ls_ayahnquran.append(n_ayah)
            n_ayah += 1 

        for i in range(1, inf["surahe"] - inf["surahs"]):
            surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1+i}").text)
            for j in range(len(surah["ayahs"])):
                try:
                    ls_ayahnquran.append(n_ayah)
                    n_ayah += 1 

                except:
                    pass
                    # with open("l.txt", "a") as f:
                    #     f.writelines(f"\n{surah['name']}, {len(surah)}")

        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahe']+1}").text)
        for i in range(inf["ayahe"][0], inf["ayahe"][1]):
            ls_ayahnquran.append(n_ayah)
            n_ayah += 1 

    if length_only:
        return len(ls_ayahnquran)
    else:
        return ls_ayahnquran, len(ls_ayahnquran)

def req_juz(juz=0):
    """ 
    \n return list of surah (1-114), start_ayah(0-6235), ayah(str), read(str), trans(str), aud(link)
    \n juz 0-29
    """
    try:
        with open("inf_juz.json", "r") as f:
            inf = json.load(f)
        inf = inf[f"{juz}"]
    except:
        with open("ownlibs/inf_juz.json", "r") as f:
            inf = json.load(f)
        inf = inf[f"{juz}"]

    start_ayah = 0
    ls_surah = []
    ls_ayah = []
    ls_read = []
    ls_trans = []
    ls_aud = []

    start_ayah = inf["ayahs"][0]
    
    if inf["surahe"] - inf["surahs"] <=0 :
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1}").text)
        for i in range(inf["ayahs"][0], inf["ayahs"][1]):
            ls_surah.append(surah["number"])
            ls_ayah.append(surah["ayahs"][i]["ayahText"])
            ls_read.append(surah["ayahs"][i]["readText"])
            ls_trans.append(surah["ayahs"][i]["enText"])
            ls_aud.append(surah["ayahs"][i]["audio"])
    elif 0 < inf["surahe"] - inf["surahs"] < 2:
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1}").text)
        for i in range(inf["ayahs"][0], inf["ayahs"][1]):
            ls_surah.append(surah["number"])
            ls_ayah.append(surah["ayahs"][i]["ayahText"])
            ls_read.append(surah["ayahs"][i]["readText"])
            ls_trans.append(surah["ayahs"][i]["enText"])
            ls_aud.append(surah["ayahs"][i]["audio"])

        
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahe']+1}").text)
        for i in range(inf["ayahe"][0], inf["ayahe"][1]):
            ls_surah.append(surah["number"])
            ls_ayah.append(surah["ayahs"][i]["ayahText"])
            ls_read.append(surah["ayahs"][i]["readText"])
            ls_trans.append(surah["ayahs"][i]["enText"])
            ls_aud.append(surah["ayahs"][i]["audio"])

    else:
        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1}").text)
        for i in range(inf["ayahs"][0], inf["ayahs"][1]):
            ls_surah.append(surah["number"])
            ls_ayah.append(surah["ayahs"][i]["ayahText"])
            ls_read.append(surah["ayahs"][i]["readText"])
            ls_trans.append(surah["ayahs"][i]["enText"])
            ls_aud.append(surah["ayahs"][i]["audio"])


        for i in range(1, inf["surahe"] - inf["surahs"]):
            surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahs']+1+i}").text)
            for j in range(len(surah["ayahs"])):
                try:
                    ls_surah.append(surah["number"])
                    ls_ayah.append(surah["ayahs"][j]["ayahText"])
                    ls_read.append(surah["ayahs"][j]["readText"])
                    ls_trans.append(surah["ayahs"][j]["enText"])
                    ls_aud.append(surah["ayahs"][i]["audio"])

                except:
                    pass
                    # with open("l.txt", "a") as f:
                    #     f.writelines(f"\n{surah['name']}, {len(surah)}")

        surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{inf['surahe']+1}").text)
        for i in range(inf["ayahe"][0], inf["ayahe"][1]):
            ls_surah.append(surah["number"])
            ls_ayah.append(surah["ayahs"][i]["ayahText"])
            ls_read.append(surah["ayahs"][i]["readText"])
            ls_trans.append(surah["ayahs"][i]["enText"])
            ls_aud.append(surah["ayahs"][i]["audio"])


    return ls_surah, start_ayah, ls_ayah, ls_read, ls_trans, ls_aud


def get_juz_by_ayahnquran(ayahnquran=0):
    """return int of juz 0-29"""
    with open("ownlibs\\inf_juz.json", "r") as f:
        inf = json.load(f)
    
    temp = 0
    pos = 0
    for i in range(len(inf)):
        pos = i
        temp+=inf[f"{i}"]["ayahn"]
        if temp-1 >= ayahnquran:
            break
    return pos

def req_murottal(surah_number=1):
    ls_link = []
    surah = json.loads(requests.get(f"https://quranapi.idn.sch.id/surah/{surah_number}").text)
    surah = surah["ayahs"]
    for i in range(len(surah)):
        ls_link.append(surah[i]["audio"])

    return ls_link

def loc2utc(locdate=datetime.now()):
    utc_offset = datetime.utcnow() - datetime.now()
    utc_datetime = locdate + utc_offset
    utc_datetime = utc_datetime.strftime("%d-%m-%Y %H:%M:00")
    return datetime.strptime(utc_datetime, "%d-%m-%Y %H:%M:00")

def utc2loc(utcdate=datetime.utcnow(), caller=None): #caller=None for jinja
    unix_epoch = time.mktime(utcdate.timetuple())
    offset = datetime.fromtimestamp(unix_epoch) - datetime.utcfromtimestamp(unix_epoch)
    local_dt = utcdate + offset
    return local_dt.strftime("%A, %d %B %Y %H:%M:00")

def sstr2list(str=""):
    """Returning list of string datatype"""
    #make list of string
    try:
        ls = str.split(",")
        while ls.count(""):
            ls.remove("")
        ls = list(ls)
    except:
        ls = []
    
    while "" in ls:
        ls.remove("")

    return ls

def str2list(str=""):
    """Returning list of int datatype"""
    #make list of string
    try:
        ls = str.split(",")
        while ls.count(""):
            ls.remove("")
        ls = list(ls)
    except:
        ls = []
    #convert each string to int
    try:
        for i in range(len(ls)):
            ls[i] = int(ls[i])
    except:
        ls = []

    return ls #datatype int

def list2str(ls=[]):
    """return the string from the list ex [0,1,2] > '0,1,2'"""
    string = ""
    try:
        for i in ls:
            string += f"{i},"
    except:
        string = ""

    return string

def add_mem_juz(member_rule="Random", mem_juz="1", data="0"):
    """return string list of added mem_juz 1-30"""

    #str 2 list
    ls = str2list(mem_juz)

    #Random
    if member_rule=="Random":
        rnd = random.randrange(1, 31)
        while rnd in ls:
            rnd = random.randrange(1, 31)
        ls.append(str(rnd))
    #Free to Choose
    elif member_rule=="Free to Choose":
        ls.append(data)
    #In Order Ascending
    elif member_rule=="In Order Ascending":
        que = 1
        while que in ls:
            que += 1
        ls.append(str(que))
    #In Order Descending
    else: #member_rule=="In Order Descending":
        que = 30
        while que in ls:
            que -= 1
        ls.append(str(que))

    #list 2 str
    ready = list2str(ls)
    return ready

def convert2wav(path=""):
    aud, sr = librosa.load(path+".webm")
    sf.write(path+".wav", aud, sr, format="wav")
    os.remove(path+".webm")

def recog(path=""):
    r = sr.Recognizer()
    aud = sr.AudioFile(path+".wav")

    with aud as source:
        audio = r.record(source)
    try:
        out = r.recognize_google(audio_data=audio, language="ar")
    except:
        out = "qwerty"
    os.remove(path+".wav")
    
    return out

def fuzz_ratio(ayah="", ayahnquran=0):
    """
    \n if ayahnquran in short_ayahs.json then
    \n return score, acc (if >= 30)
    \n else return false
    \n param ayah = ayahtext from read
    \n param ayahnquran = 0-6235
    """

    with open('ownlibs\\short_ayahs.json', 'r') as f:
        inf = json.load(f)

    with open('ownlibs\\same_ayahs.json', 'r') as f:
        inf2 = json.load(f)

    if str(ayahnquran) in list(inf.keys()): # short ayah
        t1 = inf[f'{ayahnquran}']
        t1 = araby.strip_diacritics(t1)
        if fuzz.ratio(ayah, t1) >= 30:
            return fuzz.ratio(ayah, t1)/100, True
        else:
            return fuzz.ratio(ayah, t1)/100, False
    elif str(ayahnquran) in list(inf2.keys()): # same ayah
        t1 = inf2[f'{ayahnquran}']['ls_ayah'][0]
        t1 = araby.strip_diacritics(t1)
        if fuzz.ratio(ayah, t1) >= 30:
            return fuzz.ratio(ayah, t1)/100, True
        else:
            return fuzz.ratio(ayah, t1)/100, False
    else:
        return -1, False

def predict(ayah="", ayah_number=0):
    """
    \n return score and is acc using AI except for too short ayah or same ayah
    \n param ayah_number = ayahnquran from 0-6235"""

    model = tf.keras.models.load_model("modelv3.1.h5")
    ayah = araby.strip_diacritics(ayah)

    with open("fitted.pickle", "rb") as f:
        vectorizer = pickle.load(f)

    response = vectorizer.transform([ayah])
    response = response.todense()
    result = model.predict(response)

    # if result[0][ayah_number] >= 0.5:
    #     acc = True
    # else:
    #     acc = False
    
    # return result[0][ayah_number], acc
    
    if result[0][ayah_number] >= 0.5: #predict using AI for most ayah
        acc = True
        return result[0][ayah_number], acc
    else: #predict using thefuzz for short and same ayah
        sc, acc = fuzz_ratio(ayah=ayah, ayahnquran=ayah_number)
        if sc <=0:
            return result[0][ayah_number], acc
        else:
            return sc, acc


def get_tier(aprules=[0,1], tier_names=["Jahanam"], ap=0):
    """
    \nreturning string of tier names 
    \nimage tier index from 0 to 7
    """

    if ap < aprules[0]:
        return "Unclassified", 0
    elif ap >= aprules[-1]:
        return tier_names[-1], 1
    else:
        for i in range(1, len(aprules)):
            if aprules[i-1] <= ap < aprules[i]:
                return tier_names[i-1], (8-i)

def sec2time(seconds):
    """
    \n return str time (hh:mm:ss), str hours, str minutes, str sec
    """
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    time = "%d:%02d:%02d" % (hour, minutes, seconds)
      
    return time, hour, minutes, seconds
