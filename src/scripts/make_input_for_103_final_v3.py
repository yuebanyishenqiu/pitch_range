#!/usr/bin/env python
# coding: utf-8

# In[13]:

import json
import codecs
import os
import numpy as np
import h5py

def load_data(fin):
    
    fp = codecs.open(fin, "r", encoding = "utf8")
    data = fp.readlines()
    fp.close()
    
    return data

def make_data_idxs(data):
    
    idxs = []
    for i in range(len(data)):
        line = data[i]
        if "[" in line:
            idxs.append(i)
            
    return idxs

def load_dic(src):
    
    dic = {}

    #data = load_data(src+"/../103_v4_test.targets")
    data = load_data(src+"/../103_all_test.targets")
    for line in data:
        line = line.strip().split()
        spk = line[0]
        mean = float(line[1])
        std = float(line[2])
        if spk not in dic:
            dic[spk] = {}
        dic[spk]["mean"] = mean
        dic[spk]["std"] = std

    for f in os.listdir(src):
         tone = f.split("_")[1]
         fin = src+os.sep+f
         data = load_data(fin)
         for line in data:
             line = line.strip().split()
             spk = line[0]
             mean = float(line[1])
             std = float(line[2])
             if spk not in dic:
                 print("spk {} not seen before".format(spk))
                 continue
             if tone not in dic[spk]:
                 dic[spk][tone] = {}
             dic[spk][tone]["mean"] = mean
             dic[spk][tone]["std"] = std
            
    return dic

def make_batches(samples):
    
    tot = len(samples)
    num_steps = 30
    
    batches = []
    
    cur = 0
    while cur+num_steps<tot:
        sample = samples[cur:cur+num_steps]
        batches.append(sample)
        cur += 5
        
    return np.array(batches)

def make_input_for_103(src, vad_feats, des):
    
    data = load_data(vad_feats)
    print("feats loaded...")
    idxs = make_data_idxs(data)
    print("idxs built ...")
    tdic = load_dic(src)
    print("targets dic loaded...")
    
    fdic = {}
#    for spk in tdic:
#        fdic[spk] = {}
#        for tone in tdic[spk]:
#            path = des+"/"+spk
#            if not os.path.exists(path):
#                os.makedirs(path)
#            fout = path+"/"+tone+"h5"
#            hdf = h5py.File(fout, "w")
#            dst = hdf.create_dataset("data", shape = (0, 30, 42), maxshape = (None, 30, 42), chunks = True, dtype = "f")
#            fdic[spk][tone] = {}
#            fdic[spk][tone]["data"] = dst
#            fdic[spk][tone]["fp"] = hdf
    dic = set()
    spkdic = {}
    for i in range(len(idxs)):
        beg = idxs[i]
        uttid = data[beg].strip().split()[0]
        if "monosyllable" not in uttid:
            print("{} is not mono".format(uttid))
            continue
        spk = uttid.split("_")[0]
        if spk not in tdic:
            print("spk: {} not in targets".format(spk))
            continue
        if spk not in dic:
            print("processing spk: {}".format(spk))
            dic.add(spk)
        if spk not in spkdic:
            spkdic[spk] = 0
        tone = uttid[-1]
        if spk not in fdic:
            fdic[spk] = {}
        if tone not in fdic[spk]:
            fdic[spk][tone] = {}
            path = des+"/"+spk
            if not os.path.exists(path):
                os.makedirs(path)
            fout = path+"/"+tone+"h5"
            hdf = h5py.File(fout, "w")
            dst = hdf.create_dataset("data", shape = (0, 30, 44), maxshape = (None, 30, 44), chunks = True, dtype = "f")
            fdic[spk][tone]["data"] = dst
            fdic[spk][tone]["fp"] = hdf
            fdic[spk][tone]["vecs"] = []

        if tone not in set(["1", "2", "3", "4"]):
            continue
        beg += 1
        end = 0
        mean = tdic[spk][tone]["mean"]
        std  = tdic[spk][tone]["std"]
        gmean = tdic[spk]["mean"]
        gstd  = tdic[spk]["std"]
        if i < len(idxs)-1:
            end = idxs[i+1] - 1
        else:
            end = len(data) - 2
        samples = data[beg: end]
        vecs = []
        for s in samples:
            s = s.strip().split()
            vec = [float(ss) for ss in s]
            vec.extend([mean, std, gmean, gstd])
            vecs.append(vec)
        fdic[spk][tone]["vecs"].extend(vecs)
        if len(fdic[spk][tone]["vecs"]) > 100:
            vecs = fdic[spk][tone]["vecs"]
            batches = make_batches(vecs)
            fdic[spk][tone]["data"].resize((fdic[spk][tone]["data"].shape[0]+batches.shape[0]), axis = 0)
            fdic[spk][tone]["data"][-batches.shape[0]:] = batches
            fdic[spk][tone]["vecs"] = []
        
#         for sample in samples:
#             sample = sample.strip().split()
#             if len(sample) != 40:
#                 print("Error! in file:{}".format(uttid))
#                 print(sample)
#                 exit(0)
#             vec = [float(v) for v in sample]
#             vec.extend([mean, std])
#             fdic[spk][tone]["data"].append(vec)

    for spk in fdic:
        for tone in fdic[spk]:
            fdic[spk][tone]["fp"].close()


    fp = codecs.open("/disk2/pwj/workspace/pitch-range/src/103_spk_less_300ms.json", "w", encoding = "utf8")
    json.dump(spkdic, fp)
    fp.close()
    print("Done with data processing")
                
    


# In[14]:


targets = "/home/pwj/103/tone_targets"
vad = "/disk2/pwj/workspace/pitch-range/src/103_vad_v2"
des = "/disk2/pwj/workspace/pitch-range/src/model/103_input_final_v3/"
make_input_for_103(targets, vad, des)


# In[ ]:




