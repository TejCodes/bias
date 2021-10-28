from gensim.summarization.summarizer import summarize
import pandas as pd
from ethnicolr import pred_wiki_name
from rake_nltk import Rake
import json
import os
import re
from gensim.models.doc2vec import Doc2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from collections import defaultdict
import gender_guesser.detector as gender
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MoreLikeThis
import spacy


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
nameslist=[]
for i in data:
    for j in i:
       name = j["_source"]["name"]
       uuid = j["_source"]["uuid"]
       firstName = name.split(" ")[0]
       surname = name.split(" ")[1]
       nameslist.append({"firstName": firstName, "surname": surname})

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
              "race":"",
              "org":org["name"]}
       mainlist[uuid] =entry

# Closing file
f.close()


# Generating Organization to experts dictionary.
f = open('C:\\Users\\ltopuser\\OneDrive - University of Edinburgh\\Documents\\Msc Project\\Social Identity\\expertise.json', encoding="utf-8")
data = json.load(f)
for i in data:
    for j in i:
           for k in j["_source"]["source"]["names"]:
               name=k["name"]
               firstName = name.split(" ")[0]
               surname = name.split(" ")[1]
               nameslist.append({"firstName": firstName, "surname": surname})

f.close()


df = pd.DataFrame(nameslist)
x = pred_wiki_name(df,lname_col="surname",fname_col="firstName")
raceDict={}
for i, row in df.iterrows():
    full_name = row['firstName'] +" "+row['surname']
    raceDict[full_name] = row['race']
for k,v in mainlist.items():
    v["race"]= raceDict[v["name"].split(" ")[0]+" "+v["name"].split(" ")[1]]


# Generating Organization to experts dictionary.
f = open('C:\\Users\\ltopuser\\OneDrive - University of Edinburgh\\Documents\\Msc Project\\Social Identity\\expertise.json', encoding="utf-8")
data = json.load(f)
org2Exp={}
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


#Schools list in the three Colleges
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

#Categorizing experts into respective schools and colleges
for k,value in org2Exp.items():
    if k in ahss:
        ahssOrg2Exp[k]=value
    if k in vm:
        vmOrg2Exp[k]=value
    if k in se:
        seOrg2Exp[k]=value

British = 0
NonBritish = 0
count=0
for k,v in ahssOrg2Exp.items():
    for i in v:
        race= mainlist[i]["race"]
        count += 1
        if race == "GreaterEuropean,British":
            British += 1
        else:
            NonBritish+=1

# print("AHSS strength", count)
# print(British/count,NonBritish/count)

British = 0
NonBritish = 0
count=0
for k,v in vmOrg2Exp.items():
    for i in v:
        count+=1
        race= mainlist[i]["race"]
        if race == "GreaterEuropean,British":
            British += 1
        else:
            NonBritish+=1
#
# print("VM strength", count)
# print(British / count, NonBritish/count)

British = 0
NonBritish = 0
count=0
for k,v in seOrg2Exp.items():
    for i in v:
        count+=1
        race= mainlist[i]["race"]
        if race == "GreaterEuropean,British":
            British += 1
        else:
            NonBritish+=1

# print("SE strength", count)
# print(British / count, NonBritish/count)





#Generating schools (under AHSS college) to Experts dictionary
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
#Generating AHSS college to Documents dictionary
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


    new_contr={}
    British = 0
    NonBritish=0
    count=0
    for i in contr.keys():
        race = mainlist[i]["race"]
        new_contr[i] = {"contribution_score": contr[i],
                        "race": race}
        count += 1
        if race == "GreaterEuropean,British":
            British += 1
        else:
            NonBritish+=1
    distr=[British / count, NonBritish/count]
    entry = { "distr": distr}
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
        n = random.randrange(50,75)
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

with open('ahss_etn_queries.txt', 'w') as json_file:
  json.dump(ahssOrgExp2Queries, json_file)

print()
print()
print("---------British to Non-British Distribution ratio accross schools---------")
results={}
results["school_distr"]={}
results["school_distr"]["ahss"]=ahssMF
for k, v in ahssMF.items():
    print(k, v)

#Generating schools (under vm college) to Experts dictionary
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

namDic={}
vmMF={}
vmOrg2expContri={}
#Generating vm college to Documents dictionary
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

    if k == "Edinburgh Medical School":
        new_contr = {}
        British = 0
        NonBritish = 0
        count = 0
        for i in contr.keys():
            race = mainlist[i]["race"]
            namDic[mainlist[i]["name"]] =mainlist[i]["race"]
            new_contr[i] = {"contribution_score": contr[i],
                            "race": race}
            count += 1
            if race == "GreaterEuropean,British":
                British += 1
            else:
                NonBritish += 1
        distr = [British / count, NonBritish / count]
        entry = {"distr": distr}
        vmMF[k] = entry
        vmOrg2expContri[k] = new_contr
    else:
        new_contr = {}
        British = 0
        NonBritish = 0
        count = 0
        for i in contr.keys():
            race = mainlist[i]["race"]
            new_contr[i] = {"contribution_score": contr[i],
                            "race": race}
            count += 1
            if race == "GreaterEuropean,British":
                British += 1
            else:
                NonBritish += 1
        distr = [British / count, NonBritish / count]
        entry = {"distr": distr}
        vmMF[k] = entry
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

with open('vm_etn_queries.txt', 'w') as json_file:
  json.dump(vmOrgExp2Queries, json_file)

results["school_distr"]["vm"]=vmMF
for k, v in vmMF.items():
    print(k, v)

#Generating schools (under se college) to Experts dictionary
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
#Generating se college to Documents dictionary
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


    new_contr={}
    api=0
    British = 0
    NonBritish=0
    count=0
    for i in contr.keys():
        race = mainlist[i]["race"]
        new_contr[i] = {"contribution_score": contr[i],
                        "race": race}
        count += 1
        if race == "GreaterEuropean,British":
            British += 1
        else:
            NonBritish+=1
    distr = [British / count, NonBritish/count]
    entry = { "distr": distr}
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

with open('se_etn_queries.txt', 'w') as json_file:
  json.dump(seOrgExp2Queries, json_file)

results["school_distr"]["se"]=seMF
for k, v in seMF.items():
    print(k, v)


with open('../common_files/exp_dict.json') as fp:
    exp_dict=json.load( fp)

print()
print()
print( "------average publishing ratio -----------")

results["avg_publishing_ratio"]={}
results["avg_publishing_ratio"]["ahss"]={}
results["avg_publishing_ratio"]["vm"]={}
results["avg_publishing_ratio"]["se"]={}


for k,v in ahssOrg2Exp.items():
    british = 0
    nonBritish = 0

    british_t = 0
    nonBritish_t = 0

    for i in v:
        name = mainlist[i]["name"]
        race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
        if race == "GreaterEuropean,British":
            if i not in exp_dict.keys():
                continue
            british +=exp_dict[i]
            british_t+=1
        else:
            if i not in exp_dict.keys():
                continue
            nonBritish +=exp_dict[i]
            nonBritish_t+=1

    print(k,(british/british_t)/(nonBritish/nonBritish_t))
    results["avg_publishing_ratio"]["ahss"][k] =(british/british_t)/(nonBritish/nonBritish_t)

for k,v in vmOrg2Exp.items():
    british = 0
    nonBritish = 0

    british_t = 0
    nonBritish_t = 0

    for i in v:
        name = mainlist[i]["name"]
        race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
        if race == "GreaterEuropean,British":
            if i not in exp_dict.keys():
                continue
            british +=exp_dict[i]
            british_t+=1
        else:
            if i not in exp_dict.keys():
                continue
            nonBritish +=exp_dict[i]
            nonBritish_t+=1

    print(k,(british/british_t)/(nonBritish/nonBritish_t))
    results["avg_publishing_ratio"]["vm"][k] = (british / british_t) / (nonBritish / nonBritish_t)

for k,v in seOrg2Exp.items():
    british = 0
    nonBritish = 0

    british_t = 0
    nonBritish_t = 0

    for i in v:
        name = mainlist[i]["name"]
        race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
        if race == "GreaterEuropean,British":
            if i not in exp_dict.keys():
                continue
            british +=exp_dict[i]
            british_t+=1
        else:
            if i not in exp_dict.keys():
                continue
            nonBritish +=exp_dict[i]
            nonBritish_t+=1

    print(k, (british/british_t)/(nonBritish/nonBritish_t))
    results["avg_publishing_ratio"]["se"][k] = (british / british_t) / (nonBritish / nonBritish_t)


nlp = spacy.load('en_core_web_lg')
# model = Doc2Vec.load(os.path.join(settings.BASE_DIR, 'models/doc2vec.model'), mmap='r')
MODEL_PATH = "../"

with open('../common_files/constants.json') as f:
    constants = json.load(f)
es = Elasticsearch([{'host': constants["ES_HOST_URL"], 'port':constants["ES_PORT"]}])


def get_document(doc_id):
    s = Search().using(es).index('expertise').query("match", document_id=doc_id)
    response = s.execute()
    if response.hits.total.value > 0:
        return response.to_dict()['hits']['hits'][0]['_source']
    return None


def get_person(person_id):
    response = es.search(index='experts',
                         body={
                             "query": {
                                 "match": {"uuid": person_id}
                             }
                         }
                         )
    if response['hits']['hits']:
        return response['hits']['hits'][0]['_source']
    else:
        return None


def more_like_this(text, topn=10000):
    s = Search().using(es).query(MoreLikeThis(
        like=text,
        fields=['abstract', 'tech_abstract', 'impact'],
        min_term_freq=1,
        max_query_terms=12))
    response = s.execute()
    results = defaultdict(int)
    for d in s[:topn]:
        results[d.document_id] = max(results[d.document_id], d.meta.score)
    return [(k, v) for k, v in results.items()]


def stem_text(text):
    p = PorterStemmer()
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE)  # remove email
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE)  # remove web addresses
    text = re.sub("\'", "", text)  # remove single quotes
    text = remove_stopwords(text)
    text = p.stem_sentence(text)
    return simple_preprocess(text, deacc=True)


def clean_text(corpus):
    # --- remove if not alphanumeric:
    corpus = re.sub('[\W_]+', ' ', corpus)
    # --- replace numbers with #
    corpus = re.sub(r'\b\d+\b', '#', corpus)
    # --- remove new line character
    corpus = re.sub('\n', ' ', corpus)
    # --- remove words containing numbers
    corpus = re.sub('\w*\d\w*', '', corpus)
    # --- remove one-letter words in square brackets
    corpus = re.sub(r"\b[a-zA-Z]\b", '', corpus)
    # --- remove words with one characters
    corpus = re.sub(r"\b\w{1}\b", '', corpus)
    # --- remove multiple spaces in string
    corpus = re.sub(' +', ' ', corpus)
    # --- make lowercase
    corpus = corpus.lower()
    corpus = nlp(corpus)

    all_texts = []
    for sentence in list(corpus.sents):
        # --- lemmatization, remove punctuation
        txt = [token.lemma_ for token in sentence if not token.is_punct and not token.is_stop]
        all_texts.append(txt)
    return [val for sublist in all_texts for val in sublist]


def most_similar(model, text, clean_func=clean_text, topn=None):
    vector = model.infer_vector(clean_func(text), epochs=100, alpha=model.alpha, min_alpha=model.min_alpha)
    simdocs = model.docvecs.most_similar(positive=[vector], topn=topn)
    return simdocs


def load_model(filename):
    try:
        return Doc2Vec.load(os.path.join(MODEL_PATH, filename), mmap='r')
    except:
        return None


def add(a, b):
    c = []
    for i in range(len(a)):
        c.append(a[i] + b[i])
    return c


def mult(a, b):
    c = []
    for i in range(len(a)):
        c.append(a[i] * b)
    return c



if __name__ == "__main__":
    model = load_model('doc2vec_roag.model')
    print("-------------------------------Tf Idf--------------------- ")

    with open('ahss_etn_queries.txt') as f:
        data = json.load(f)

    ahss={}
    for k,v in data.items():
        count = 0
        sum = [0.0,0.0]
        for a,b in v.items():
            for g,h in b.items():
                text = h["short_query"]
                if len(text)==0:
                    print("no Query")
                tf_idf = more_like_this(text, topn=20)
                docs=0
                weights= [ 512/1023,256/1023,128/1023,64/1023,32/1023,16/1023,8/1023,4/1023,2/1023,1/1023 ]
                weighted_distr=[0.0,0.0]

                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"] )>0:

                        British=0
                        NonBritish=0
                        for i in document["source"]["names"] :
                            name = i["name"]
                            race = raceDict[name.split(" ")[0]+" "+name.split(" ")[1]]
                            if race == "GreaterEuropean,British":
                                British += 1
                            else:
                                NonBritish += 1
                        total= British+NonBritish
                        distr= [British*weights[docs]/total,NonBritish*weights[docs]/total]
                        weighted_distr= add( distr,weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum =add(sum,weighted_distr)
                count+=1
        for i in range(len(sum)):
            sum[i]=sum[i]/count

        ahss[k]=  {
            "distr":sum}

    results["tfIdf"]={}
    results["doc2vec"]={}
    results["tfIdf"]["ahss"]=ahss
    for k,v in ahss.items():
        print(v["distr"])

    with open('vm_etn_queries.txt') as f:
        data = json.load(f)

    vm = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["short_query"]
                if len(text) == 0:
                    print("no Query")
                tf_idf = more_like_this(text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0]

                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:

                        British = 0
                        NonBritish = 0
                        for i in document["source"]["names"]:
                            name = i["name"]
                            race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
                            if race == "GreaterEuropean,British":
                                British += 1
                            else:
                                NonBritish += 1
                        total = British + NonBritish
                        distr = [British * weights[docs] / total, NonBritish * weights[docs] / total]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        vm[k] = {
            "distr": sum}

    results["tfIdf"]["vm"] = vm
    for k, v in vm.items():
        print(v["distr"])

    with open('se_etn_queries.txt') as f:
        data = json.load(f)

    se = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["short_query"]
                if len(text) == 0:
                    print("no Query")
                tf_idf = more_like_this(text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0]

                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:

                        British = 0
                        NonBritish = 0
                        for i in document["source"]["names"]:
                            name = i["name"]
                            race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
                            if race == "GreaterEuropean,British":
                                British += 1
                            else:
                                NonBritish += 1
                        total = British + NonBritish
                        distr = [British * weights[docs] / total, NonBritish * weights[docs] / total]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        se[k] = {
            "distr": sum}

    results["tfIdf"]["se"] = se
    for k, v in se.items():
        print(v["distr"])


    print("--------------doc2vec-----------------------")
    with open('ahss_etn_queries.txt') as f:
        data = json.load(f)

    ahss = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0]

                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:

                        British = 0
                        NonBritish = 0
                        for i in document["source"]["names"]:
                            name = i["name"]
                            race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
                            if race == "GreaterEuropean,British":
                                British += 1
                            else:
                                NonBritish += 1
                        total = British + NonBritish
                        distr = [British * weights[docs] / total, NonBritish * weights[docs] / total]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        ahss[k] = {
            "distr": sum}
    results["doc2vec"]["ahss"] = ahss
    for k, v in ahss.items():
        print(v["distr"])

    with open('vm_etn_queries.txt') as f:
        data = json.load(f)

    vm = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0]

                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:

                        British = 0
                        NonBritish = 0
                        for i in document["source"]["names"]:
                            name = i["name"]
                            race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
                            if race == "GreaterEuropean,British":
                                British += 1
                            else:
                                NonBritish += 1
                        total = British + NonBritish
                        distr = [British * weights[docs] / total, NonBritish * weights[docs] / total]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        vm[k] = {
            "distr": sum}
    results["doc2vec"]["vm"] = vm
    for k, v in vm.items():
        print(v["distr"])

    with open('se_etn_queries.txt') as f:
        data = json.load(f)

    se = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0]

                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:

                        British = 0
                        NonBritish = 0
                        for i in document["source"]["names"]:
                            name = i["name"]
                            race = raceDict[name.split(" ")[0] + " " + name.split(" ")[1]]
                            if race == "GreaterEuropean,British":
                                British += 1
                            else:
                                NonBritish += 1
                        total = British + NonBritish
                        distr = [British * weights[docs] / total, NonBritish * weights[docs] / total]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        se[k] = {
            "distr": sum}

    results["doc2vec"]["se"] = se
    for k, v in se.items():
        print(v["distr"])

with open('ethnic_bias_results.json', 'w') as json_file:
    json.dump(results, json_file, indent=4)