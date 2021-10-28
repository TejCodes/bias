import json
import gender_guesser.detector as gender
from gensim.summarization.summarizer import summarize
import pandas as pd

from rake_nltk import Rake
import re



# Opening JSON file
f = open('C:\\Users\\ltopuser\\OneDrive - University of Edinburgh\Documents\\Msc Project\\Social Identity\\experts.json', encoding="utf-8")

contribution_threshold= 5.0
data = json.load(f)

d = gender.Detector()
mainlist={}
orgs={}


id=0
g=0
count=0
bigOrgs =["College of Arts, Humanities and Social Sciences","College of Medicine and Veterinary Medicine","College of Science and Engineering"]
for i in data:
    for j in i:
       name = j["_source"]["name"]
       uuid = j["_source"]["uuid"]
       firstName = name.split(" ")[0]
       gender = d.get_gender(firstName)  #Gender Idenitification

       if j["_source"]["organisations"][0]["name"] in bigOrgs:
           if len(j["_source"]["organisations"]) >1:
                org = j["_source"]["organisations"][1]
                count += 1
           else:
               org = j["_source"]["organisations"][0]

       else:
            org = j["_source"]["organisations"][0]
       entry={
              "name": name,
              "experience_score":0,
              "gender": gender,
              "org":org["name"]}
       mainlist[uuid] =entry

# Closing file
f.close()


# Opening JSON file
f = open('C:\\Users\\ltopuser\\OneDrive - University of Edinburgh\\Documents\\Msc Project\\Social Identity\\expertise.json', encoding="utf-8")
data = json.load(f)
org2Exp={}
exp_dict={}
for i in data:
    for j in i:
        for k in j["_source"]["experts"]:
                if k in exp_dict:
                    exp_dict[k] += 1 / len(j["_source"]["experts"])

                else:
                    exp_dict[k]=1/len(j["_source"]["experts"])
min=1000000
max=0
sum=0
c=0
t=0
u=0
ve=0
z=0
for k,v in exp_dict.items():
    c+=1
    sum+=v
    if v>max:
        max=v
    if v<min:
        min=v
    if v<7:   #beginner
        t+=1
    if v>=7 and v<30: #moderate
        u+=1
    if v>=30 and v<100: #experienced
        ve+=1
    if v >= 100:  #very expereinced
        z+=1

print("beginner",t)
print("moderate",u)
print("expereinced",ve)
print("very expereinced",z)
print("min contribution score",min)
print("max contribution score",max)
print("avg contribution score",sum/c)


for k,i in mainlist.items():
    if i["org"] not in org2Exp.keys():
        org2Exp[i["org"]] = [k]
    else:
        org2Exp[i["org"]].append(k)

# adding subschools experts to their schools
org2Exp["School of Biological Sciences"].extend(org2Exp["EastBio (East of Scotland Bioscience Doctoral Training Partnership)"])
org2Exp["School of Informatics"].extend(org2Exp["Data Science CDT"])
org2Exp["School of Informatics"].extend(org2Exp["Neuroinformatics DTC"])
del org2Exp["Neuroinformatics DTC"]
del org2Exp["Data Science CDT"]
del org2Exp["EastBio (East of Scotland Bioscience Doctoral Training Partnership)"]


ahss = ["Business School","Edinburgh College of Art","Moray House School of Education and Sport",
        "School of Economics","School of Divinity","School of Law","School of Philosophy",
        "Psychology and Language Sciences","School of Social and Political Science","School of History, Classics and Archaeology",
        "School of Literatures, Languages and Cultures"]
vm=["Deanery of Biomedical Sciences","Deanery of Clinical Sciences",
    "Deanery of Molecular, Genetic and Population Health Sciences",
    "Royal (Dick) School of Veterinary Studies"]
se=["School of Biological Sciences","School of Informatics","School of Engineering",
    "School of Chemistry","School of Physics and Astronomy","School of Geosciences"]
ahssOrg2Exp ={}
vmOrg2Exp={}
seOrg2Exp ={}

for k,value in org2Exp.items():
    if k in ahss:
        ahssOrg2Exp[k]=value
    if k in vm:
        vmOrg2Exp[k]=value
    if k in se:
        seOrg2Exp[k]=value


a=0
b=0
c=0
d=0
t=0
for k, v in ahssOrg2Exp.items():
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=1
        if v > 7 and v < 30:  # moderate
            b+=1
        if v > 30 and v < 100:  # experienced
            c+=1
        if v > 100:  # very experienced
            d+=1
    t=a+b+c+d
print()
print("AHSS distribution:")
print(a/t,b/t,c/t,d/t)
print("ahss strength", t)



a=0
b=0
c=0
d=0
t=0
for k, v in vmOrg2Exp.items():
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=1
        if v > 7 and v < 30:  # moderate
            b+=1
        if v > 30 and v < 100:  # experienced
            c+=1
        if v > 100:  # very experienced
            d+=1
    t=a+b+c+d
print()
print("VM distribution:")
print(a/t,b/t,c/t,d/t)
print("vm strength", t)



a=0
b=0
c=0
d=0
t=0
for k, v in seOrg2Exp.items():
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=1
        if v > 7 and v < 30:  # moderate
            b+=1
        if v > 30 and v < 100:  # experienced
            c+=1
        if v > 100:  # very experienced
            d+=1
    t=a+b+c+d

print()
print("SE distribution:")
print(a/t,b/t,c/t,d/t)
print("se strength", t)

ahssOrg2Docs={}
for key,v in ahssOrg2Exp.items():
    experts = ahssOrg2Exp[key]
    docs = []
    for i in data:
        for j in i:
            flag = True
            for k in j["_source"]["experts"]:
                if k not in experts:
                    flag = False
                    break
            if flag == True:
                docs.append(j)
    ahssOrg2Docs[key] =docs



ahssMF={}
ahssOrg2expContri={}
for k,h in ahssOrg2Docs.items():
    contr = {}
    for v in h:
        for i in v["_source"]["experts"]:
            if i in contr.keys():
                contr[i]+=1/len(v["_source"]["experts"])
            else:
                contr[i]=1/len(v["_source"]["experts"])
    deleteList = []
    for a,b in contr.items():
        if b <contribution_threshold:
            deleteList.append(a)
    for i in deleteList:
        del contr[i]


    genderUnknownList=[]
    new_contr={}
    a=0
    b=0
    c=0
    d=0
    for i in contr.keys():
        v = exp_dict[i]
        new_contr[i] = {"contribution_score": contr[i],
                        "exp": v}
        if v <7:
            a+=1
        if v > 7 and v < 30:  # moderate
            b+=1
        if v > 30 and v < 100:  # experienced
            c+=1
        if v > 100:  # very experienced
            d+=1
    t=a+b+c+d
    entry = {"distr": [a/t,b/t,c/t,d/t]}
    ahssMF[k]=entry
    ahssOrg2expContri[k] = new_contr

ahssOrgExp2Doc={}
for k,v in ahssOrg2Docs.items():
    ahssOrgExp2Doc[k] ={}
    for doc in v:
        for exp in doc["_source"]["experts"]:
            if exp in ahssOrgExp2Doc[k].keys():
                ahssOrgExp2Doc[k][exp].append(doc)
            else:
                ahssOrgExp2Doc[k][exp]= [doc]


ahssOrgExp2DocQueries={}
for k,v in ahssOrg2expContri.items():
    for j in v.keys():
        for m in ahssOrgExp2Doc[k][j]:
            if len (m["_source"]["experts"]) ==1:
                if k in ahssOrgExp2DocQueries.keys():
                    if j in ahssOrgExp2DocQueries[k].keys():
                        ahssOrgExp2DocQueries[k][j].append(m)
                    else:
                        ahssOrgExp2DocQueries[k][j] =[m]
                else:
                    ahssOrgExp2DocQueries[k]={}
                    ahssOrgExp2DocQueries[k][j] =[m]

import random

r = Rake()  # Uses stopwords for english from NLTK, and all punctuation characters.

def genShortQuery(abs,title):

    r.extract_keywords_from_text(title)
    title_phrases = r.get_ranked_phrases()
    try:
        summarized_abstract = summarize(abs, word_count=50)
        r.extract_keywords_from_text(summarized_abstract)
        abstract_phrases = r.get_ranked_phrases()
    except:
        abstract_phrases=[]
    i = len(title_phrases)
    j =len(abstract_phrases)
    a=0
    b=0
    string=""
    for k in range(i+j):
        if a <i:
            string+=title_phrases[a]+" "
            a+=1
        if b< j:
            string+=abstract_phrases[b]+" "
            b+=1
    list  = string.split(" ")
    if len(list) >25:
        return ' '.join(word for word in list[:24])
    else :
        return ' '.join(word for word in list)


def genLongQuery(abs):
    try :
        n = random.randrange(50,250)
        return summarize(abs, word_count=n)
    except :
        return abs

def clean_text(corpus):

    # --- replace numbers with #
    corpus = re.sub(r'\b\d+\b', '#', corpus)
    # --- remove new line character
    corpus = re.sub('\n', ' ', corpus)

    corpus = re.sub('<','',corpus)
    corpus = re.sub('>', ' ', corpus)
    corpus = re.sub('/', '', corpus)
    # --- make lowercase
    corpus = corpus.lower()

    return corpus

ahssOrgExp2Queries={}
for k,v in ahssOrgExp2DocQueries.items():
    ahssOrgExp2Queries[k]={}
    for a,b in v.items():
        indexes =[]
        if len(b)>=3:
            count=0

            l  =list(range(len(b)))
            random.shuffle(l)
            for i in l:
                if b[i]["_source"]["abstract"] != "":
                    indexes.append(i)
                    count+=1
                if count==3:
                    break
        else:
            indexes = range(len(b))
        for i in indexes:
            abstract = clean_text(b[i]["_source"]["abstract"])
            tfQuery = genShortQuery(abstract,b[i]["_source"]["title"])
            docQuery = genLongQuery(abstract)
            entry = { "short_query": tfQuery,
                      "long_query": docQuery}

            if a in ahssOrgExp2Queries[k]:
                ahssOrgExp2Queries[k][a][b[i]["_id"]] = entry
            else:
                ahssOrgExp2Queries[k][a] = {}
                ahssOrgExp2Queries[k][a][b[i]["_id"]] = entry

with open('ahss_exp_queries.txt', 'w') as json_file:
  json.dump(ahssOrgExp2Queries, json_file)

results={}
results["school_distr"] ={}
results["school_distr"]["ahss"]=ahssMF
for k, v in ahssMF.items():
    print(k, v)


vmOrg2Docs={}
for key,v in vmOrg2Exp.items():
    experts = vmOrg2Exp[key]
    docs = []
    for i in data:
        for j in i:
            flag = True
            for k in j["_source"]["experts"]:
                if k not in experts:
                    flag = False
                    break
            if flag == True:
                docs.append(j)
    vmOrg2Docs[key] =docs



vmMF={}
vmOrg2expContri={}
for k,h in vmOrg2Docs.items():
    contr = {}
    for v in h:
        for i in v["_source"]["experts"]:
            if i in contr.keys():
                contr[i]+=1/len(v["_source"]["experts"])
            else:
                contr[i]=1/len(v["_source"]["experts"])
    deleteList = []
    for a,b in contr.items():
        if b <contribution_threshold:
            deleteList.append(a)
    for i in deleteList:
        del contr[i]


    genderUnknownList=[]
    new_contr={}
    a=0
    b=0
    c=0
    d=0
    for i in contr.keys():
        v = exp_dict[i]
        new_contr[i] = {"contribution_score": contr[i],
                        "exp": v}
        if v <7:
            a+=1
        if v > 7 and v < 30:  # moderate
            b+=1
        if v > 30 and v < 100:  # experienced
            c+=1
        if v > 100:  # very experienced
            d+=1
    t=a+b+c+d
    entry = {"distr": [a/t,b/t,c/t,d/t]}
    vmMF[k]=entry
    vmOrg2expContri[k] = new_contr

vmOrgExp2Doc={}
for k,v in vmOrg2Docs.items():
    vmOrgExp2Doc[k] ={}
    for doc in v:
        for exp in doc["_source"]["experts"]:
            if exp in vmOrgExp2Doc[k].keys():
                vmOrgExp2Doc[k][exp].append(doc)
            else:
                vmOrgExp2Doc[k][exp]= [doc]


vmOrgExp2DocQueries={}
for k,v in vmOrg2expContri.items():
    for j in v.keys():
        for m in vmOrgExp2Doc[k][j]:
            if len (m["_source"]["experts"]) ==1:
                if k in vmOrgExp2DocQueries.keys():
                    if j in vmOrgExp2DocQueries[k].keys():
                        vmOrgExp2DocQueries[k][j].append(m)
                    else:
                        vmOrgExp2DocQueries[k][j] =[m]
                else:
                    vmOrgExp2DocQueries[k]={}
                    vmOrgExp2DocQueries[k][j] =[m]


vmOrgExp2Queries={}
for k,v in vmOrgExp2DocQueries.items():
    vmOrgExp2Queries[k]={}
    for a,b in v.items():
        indexes =[]
        if len(b)>=3:
            count=0

            l  =list(range(len(b)))
            random.shuffle(l)
            for i in l:
                if b[i]["_source"]["abstract"] != "":
                    indexes.append(i)
                    count+=1
                if count==3:
                    break
        else:
            indexes = range(len(b))

        for i in indexes:
            abstract = clean_text(b[i]["_source"]["abstract"])
            tfQuery = genShortQuery(abstract,b[i]["_source"]["title"])
            docQuery = genLongQuery(abstract)
            entry = { "short_query": tfQuery,
                      "long_query": docQuery}
            if a in vmOrgExp2Queries[k]:
                vmOrgExp2Queries[k][a][b[i]["_id"]] = entry
            else:
                vmOrgExp2Queries[k][a] = {}
                vmOrgExp2Queries[k][a][b[i]["_id"]] = entry

with open('vm_exp_queries.txt', 'w') as json_file:
  json.dump(vmOrgExp2Queries, json_file)

results["school_distr"]["vm"]=vmMF
for k, v in vmMF.items():
    print(k, v)


seOrg2Docs={}
for key,v in seOrg2Exp.items():
    experts = seOrg2Exp[key]
    docs = []
    for i in data:
        for j in i:
            flag = True
            for k in j["_source"]["experts"]:
                if k not in experts:
                    flag = False
                    break
            if flag == True:
                docs.append(j)
    seOrg2Docs[key] =docs



seMF={}
seOrg2expContri={}
for k,h in seOrg2Docs.items():
    contr = {}
    for v in h:
        for i in v["_source"]["experts"]:
            if i in contr.keys():
                contr[i]+=1/len(v["_source"]["experts"])
            else:
                contr[i]=1/len(v["_source"]["experts"])
    deleteList = []
    for a,b in contr.items():
        if b <contribution_threshold:
            deleteList.append(a)
    for i in deleteList:
        del contr[i]


    genderUnknownList=[]
    new_contr={}
    a=0
    b=0
    c=0
    d=0
    for i in contr.keys():
        v = exp_dict[i]
        new_contr[i] = {"contribution_score": contr[i],
                        "exp": v}
        if v <7:
            a+=1
        if v > 7 and v < 30:  # moderate
            b+=1
        if v > 30 and v < 100:  # experienced
            c+=1
        if v > 100:  # very experienced
            d+=1
    t=a+b+c+d
    entry = {"distr": [a/t,b/t,c/t,d/t]}
    seMF[k]=entry
    seOrg2expContri[k] = new_contr

seOrgExp2Doc={}
for k,v in seOrg2Docs.items():
    seOrgExp2Doc[k] ={}
    for doc in v:
        for exp in doc["_source"]["experts"]:
            if exp in seOrgExp2Doc[k].keys():
                seOrgExp2Doc[k][exp].append(doc)
            else:
                seOrgExp2Doc[k][exp]= [doc]


seOrgExp2DocQueries={}
for k,v in seOrg2expContri.items():
    for j in v.keys():
        for m in seOrgExp2Doc[k][j]:
            if len (m["_source"]["experts"]) ==1:
                if k in seOrgExp2DocQueries.keys():
                    if j in seOrgExp2DocQueries[k].keys():
                        seOrgExp2DocQueries[k][j].append(m)
                    else:
                        seOrgExp2DocQueries[k][j] =[m]
                else:
                    seOrgExp2DocQueries[k]={}
                    seOrgExp2DocQueries[k][j] =[m]


seOrgExp2Queries={}
for k,v in seOrgExp2DocQueries.items():
    seOrgExp2Queries[k]={}
    for a,b in v.items():
        indexes =[]
        if len(b)>=3:
            count=0

            l  =list(range(len(b)))
            random.shuffle(l)
            for i in l:
                if b[i]["_source"]["abstract"] != "":
                    indexes.append(i)
                    count+=1
                if count==3:
                    break
        else:
            indexes = range(len(b))

        for i in indexes:
            abstract = clean_text(b[i]["_source"]["abstract"])
            tfQuery = genShortQuery(abstract,b[i]["_source"]["title"])
            docQuery = genLongQuery(abstract)
            entry = { "short_query": tfQuery,
                      "long_query": docQuery}
            if a in seOrgExp2Queries[k]:
                seOrgExp2Queries[k][a][b[i]["_id"]] = entry
            else:
                seOrgExp2Queries[k][a] = {}
                seOrgExp2Queries[k][a][b[i]["_id"]] = entry

with open('se_exp_queries.txt', 'w') as json_file:
  json.dump(seOrgExp2Queries, json_file)

results["school_distr"]["se"]=seMF
for k, v in seMF.items():
    print(k, v)

with open('../common_files/exp_dict.json', 'w') as fp:
    json.dump(exp_dict, fp)

with open('../common_files/exp_dict.json') as fp:
    exp_dict=json.load( fp)
print()
print()
print( "------average publishing ratio -----------")

print("--------------------------a------------------------")
for k,v in ahssOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    print(a/at)
print("---------------------------b------------------------")
for k,v in ahssOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    print(b/bt)
print("---------------------------c------------------------")
for k,v in ahssOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    if ct!=0:
        print(c/ct)
    else:
        print(0)


print("---------------------------d------------------------")
for k,v in ahssOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    if dt!=0:
        print(d/dt)
    else:
        print(0)

print("--------------------------a------------------------")
for k,v in vmOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    print(a/at)
print("---------------------------b------------------------")
for k,v in vmOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    print(b/bt)
print("---------------------------c------------------------")
for k,v in vmOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    if ct!=0:
        print(c/ct)
    else:
        print(0)


print("---------------------------d------------------------")
for k,v in vmOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    if dt!=0:
        print(d/dt)
    else:
        print(0)

print("--------------------------a------------------------")
for k,v in seOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    print(a/at)
print("---------------------------b------------------------")
for k,v in seOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    print(b/bt)
print("---------------------------c------------------------")
for k,v in seOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1

    if ct!=0:
        print(c/ct)
    else:
        print(0)


print("---------------------------d------------------------")
for k,v in seOrg2Exp.items():
    a=0
    b=0
    c=0
    d=0
    at=0
    bt=0
    ct=0
    dt=0
    for i in v:
        if i in exp_dict.keys():
            v = exp_dict[i]
        else:
            v=0
        if v <7:
            a+=v
            at+=1
        if v > 7 and v < 30:  # moderate
            b+=v
            bt += 1
        if v > 30 and v < 100:  # experienced
            c+=v
            ct += 1
        if v > 100:  # very experienced
            d+=v
            dt += 1
    if dt!=0:
        print(d/dt)
    else:
        print(0)

    with open('exp_bias_results.json', 'w') as json_file:
        json.dump(results, json_file,indent=4)