import json
import gender_guesser.detector as gender
from gensim.summarization.summarizer import summarize
from rake_nltk import Rake
import random
import os
import re
from gensim.models.doc2vec import Doc2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from collections import defaultdict
import uuid
import gender_guesser.detector as gender
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MoreLikeThis
import spacy

r = Rake()  # Uses stopwords for english from NLTK, and all punctuation characters.

# Opening JSON file
f = open('C:\\Users\\ltopuser\\OneDrive - University of Edinburgh\Documents\\Msc Project\\Social Identity\\experts.json', encoding="utf-8")
data = json.load(f)

# Only professors with contribution score more than 5 are considered for analysis
contribution_threshold= 5.0

d = gender.Detector()
mainlist={}
orgs={}


#List of Organisations in University of Edinburgh
bigOrgs =["College of Arts, Humanities and Social Sciences","College of Medicine and Veterinary Medicine","College of Science and Engineering"]

# Create MainList Dictionary where 'key' is the 'UUID' of the expert and 'value' is a 'dictionary' that contains
# name , gender, experience score and the organisation of the given expert.
for i in data:
    for j in i:
       name = j["_source"]["name"]
       uuid = j["_source"]["uuid"]
       firstName = name.split(" ")[0]
       gender = d.get_gender(firstName)  #Gender Idenitification

       if j["_source"]["organisations"][0]["name"] in bigOrgs:

            #Case: where an expert belongs to Multiple Orgs, we take the second Org as the primary Org,
            #Case: where an expert belongs to a single org, we only consider that org.
           if len(j["_source"]["organisations"]) >1:
                org = j["_source"]["organisations"][1]
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
f.close()

f = open('C:\\Users\\ltopuser\\OneDrive - University of Edinburgh\\Documents\\Msc Project\\Social Identity\\expertise.json', encoding="utf-8")
data = json.load(f)
org2Exp={}

#Create a ORG2EXP dictionary where key is the Org and value is a list of all experts within that Org.
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

#List of schools of importance under a given organisation
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

#Create Org dictionaries where for each dictionary, 'key' is the 'school name'
# and 'value' is the list of experts in that school.
for k,value in org2Exp.items():
    if k in ahss:
        ahssOrg2Exp[k]=value
    if k in vm:
        vmOrg2Exp[k]=value
    if k in se:
        seOrg2Exp[k]=value


#AHSS ORG : creates a ORG2DOCS dictionary where 'key' : 'school name under the ORG'
# and 'value' :' All the documents that have authors only from the given school'.
ahssOrg2Docs={}
for key,v in ahssOrg2Exp.items():
    experts = ahssOrg2Exp[key]
    docs = []
    for i in data: # data os information loaded from expertise.json
        for j in i:
            flag = True
            for k in j["_source"]["experts"]:
                if k not in experts:
                    flag = False
                    break
            if flag == True:
                docs.append(j)
    ahssOrg2Docs[key] =docs



#AHSS ORG : caluclates contribution score of each expert in AHSS org
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
    #removes experts with contribution_score<5.0
    for a,b in contr.items():
        if b <contribution_threshold:
            deleteList.append(a)
    for i in deleteList:
        del contr[i]


    genderUnknownList=[]
    new_contr={}
    male = 0
    female = 0
    others=0
    for i in contr.keys():
        gender = mainlist[i]["gender"]
        if gender == "male" or gender == "mostly_male":
            male+=1
            new_contr[i] = {"contribution_score": contr[i],
                     "gender": gender}
        elif gender == "female" or gender=="mostly_female":
            female+=1
            new_contr[i] = {"contribution_score": contr[i],
                     "gender": gender}
        else:
            others+=1
            genderUnknownList.append(i)
    entry = {
        # "mf":male/(male+female+others),
        #     "ff": female/(male+female+others),
             "ratio": male/female}
    ahssMF[k]=entry

    #removes experts whose gender is unknown
    for i in genderUnknownList:
        del contr[i]
    ahssOrg2expContri[k] = new_contr

#AHSS : creates an expert to docs mapping for all experts within a school in given ORG
ahssOrgExp2Doc={}
for k,v in ahssOrg2Docs.items():
    ahssOrgExp2Doc[k] ={}
    for doc in v:
        for exp in doc["_source"]["experts"]:
            if exp in ahssOrgExp2Doc[k].keys():
                ahssOrgExp2Doc[k][exp].append(doc)
            else:
                ahssOrgExp2Doc[k][exp]= [doc]

#AHSS: finds all the documents for every expert in each school in which the expert is the only author.
#Creates a dictionary of all such documents for query generation.
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

#generates short query from abstract and title
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

#generates long query from abstract
def genLongQuery(abs):
    try :
        n = random.randrange(50,75)
        return summarize(abs, word_count=n)
    except :
        return abs

#helps to clean the text
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

#AHSS generates short and long queries for all the docuemnts in the ahssOrgExp2DocQueries for each expert.
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
                ahssOrgExp2Queries[k][a][b[i]["_source"]["document_id"]] = entry
            else:
                ahssOrgExp2Queries[k][a] = {}
                ahssOrgExp2Queries[k][a][b[i]["_source"]["document_id"]] = entry

with open('ahss_gender_queries.txt', 'w') as json_file:
  json.dump(ahssOrgExp2Queries, json_file)
print()
print()
print("AHSS College MF ratio:")
for k, v in ahssMF.items():
    print(k,v)

#VM ORG : creates a ORG2DOCS dictionary where 'key' : 'school name under the ORG'
# and 'value' :' All the documents that have authors only from the given school'.
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


#VM ORG : caluclates contribution score of each expert in VM org
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
    male = 0
    female = 0
    others=0
    for i in contr.keys():
        gender = mainlist[i]["gender"]
        if gender == "male" or gender == "mostly_male":
            male+=1
            new_contr[i] = {"contribution_score": contr[i],
                     "gender": gender}
        elif gender == "female" or gender=="mostly_female":
            female+=1
            new_contr[i] = {"contribution_score": contr[i],
                     "gender": gender}
        else:
            others+=1
            genderUnknownList.append(i)
    entry = {
        # "mf":male/(male+female+others),
        #     "ff": female/(male+female+others),
             "ratio": male/female}
    vmMF[k]=entry
    for i in genderUnknownList:
        del contr[i]
    vmOrg2expContri[k] = new_contr

#VM : creates an expert to docs mapping for all experts within a school in given ORG
vmOrgExp2Doc={}
for k,v in vmOrg2Docs.items():
    vmOrgExp2Doc[k] ={}
    for doc in v:
        for exp in doc["_source"]["experts"]:
            if exp in vmOrgExp2Doc[k].keys():
                vmOrgExp2Doc[k][exp].append(doc)
            else:
                vmOrgExp2Doc[k][exp]= [doc]

#VM: finds all the documents for every expert in each school in which the expert is the only author.
#Creates a dictionary of all such documents for query generation.
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

#VM: generates short and long queries for all the documents in the ahssOrgExp2DocQueries for each expert.
vmOrgExp2Queries={}
for k,v in vmOrgExp2DocQueries.items():
    vmOrgExp2Queries[k]={}
    for a,b in v.items():
        indexes =[]
        if len(b)>=3:
            count=0
            l = list(range(len(b)))
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
                vmOrgExp2Queries[k][a][b[i]["_source"]["document_id"]] = entry
            else:
                vmOrgExp2Queries[k][a] = {}
                vmOrgExp2Queries[k][a][b[i]["_source"]["document_id"]] = entry

with open('vm_gender_queries.txt', 'w') as json_file:
  json.dump(vmOrgExp2Queries, json_file)

print()
print()
print("VM College MF ratio:")
for k, v in vmMF.items():
    print(k,v)


#VM ORG : creates a ORG2DOCS dictionary where 'key' : 'school name under the ORG'
# and 'value' :' All the documents that have authors only from the given school'.
#VM ORG : caluclates contribution score of each expert in VM org
#VM : creates an expert to docs mapping for all experts within a school in given ORG
#VM: finds all the documents for every expert in each school in which the expert is the only author.
#Creates a dictionary of all such documents for query generation.
#VM: generates short and long queries for all the documents in the ahssOrgExp2DocQueries for each expert.

#SE ORG : creates a ORG2DOCS dictionary where 'key' : 'school name under the ORG'
# and 'value' :' All the documents that have authors only from the given school'.
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


#SE ORG : caluclates contribution score of each expert in SE org
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
    male = 0
    female = 0
    others=0
    for i in contr.keys():
        gender = mainlist[i]["gender"]
        if gender == "male" or gender == "mostly_male":
            male+=1
            new_contr[i] = {"contribution_score": contr[i],
                     "gender": gender}
        elif gender == "female" or gender=="mostly_female":
            female+=1
            new_contr[i] = {"contribution_score": contr[i],
                     "gender": gender}
        else:
            others+=1
            genderUnknownList.append(i)
    entry = {
        # "mf":male/(male+female+others),
        #     "ff": female/(male+female+others),
             "ratio": male/female}
    seMF[k]=entry
    for i in genderUnknownList:
        del contr[i]
    seOrg2expContri[k] = new_contr

#SE : creates an expert to docs mapping for all experts within a school in given ORG
seOrgExp2Doc={}
for k,v in seOrg2Docs.items():
    seOrgExp2Doc[k] ={}
    for doc in v:
        for exp in doc["_source"]["experts"]:
            if exp in seOrgExp2Doc[k].keys():
                seOrgExp2Doc[k][exp].append(doc)
            else:
                seOrgExp2Doc[k][exp]= [doc]

#SE: finds all the documents for every expert in each school in which the expert is the only author.
#Creates a dictionary of all such documents for query generation.
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

#SE: generates short and long queries for all the documents in the ahssOrgExp2DocQueries for each expert.
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
                seOrgExp2Queries[k][a][b[i]["_source"]["document_id"]] = entry
            else:
                seOrgExp2Queries[k][a] = {}
                seOrgExp2Queries[k][a][b[i]["_source"]["document_id"]] = entry

with open('se_gender_queries.txt', 'w') as json_file:
  json.dump(seOrgExp2Queries, json_file)

print()
print()
print("SE College MF ratio:")
for k, v in seMF.items():
    print(k,v)

results={}
results["school_MF_ratio"]={}
results["doc2vec_MF_ratio"]={}
results["tfIdf_MF_ratio"]={}
results["avg_publishing_ratio"]={}
results["school_MF_ratio"]["ahss"]=ahssMF
results["school_MF_ratio"]["vm"]=vmMF
results["school_MF_ratio"]["se"]=seMF
results["avg_publishing_ratio"]["ahss"] = {}
results["avg_publishing_ratio"]["vm"] = {}
results["avg_publishing_ratio"]["se"] = {}
results["tfIdf_MF_ratio"]["ahss"] = {}
results["doc2vec_MF_ratio"]["ahss"] = {}
results["tfIdf_MF_ratio"]["vm"] = {}
results["doc2vec_MF_ratio"]["vm"] = {}
results["tfIdf_MF_ratio"]["se"] = {}
results["doc2vec_MF_ratio"]["se"] = {}


with open('../common_files/exp_dict.json') as fp:
    exp_dict=json.load( fp)
print()
print()
print( "------average publishing ratio -----------")

#Calculates Average publishing ratio across all schools .

for k,v in ahssOrg2Exp.items():
    male_sum=0
    female_sum = 0
    male_count=0
    female_count=0
    for i in v:
        gender=mainlist[i]["gender"]
        if gender == "male" or gender == "mostly_male":
            if i not in exp_dict.keys():
                continue
            male_sum +=exp_dict[i]
            male_count+=1
        elif gender == "female" or gender == "mostly_female":
            if i not in exp_dict.keys():
                continue
            female_sum += exp_dict[i]
            female_count+=1
    print(k,(male_sum/male_count)/(female_sum/female_count))

    results["avg_publishing_ratio"]["ahss"][k] =( male_sum/male_count)/(female_sum/female_count)

for k,v in vmOrg2Exp.items():
    male_sum=0
    female_sum = 0
    male_count=0
    female_count=0
    for i in v:
        gender=mainlist[i]["gender"]
        if gender == "male" or gender == "mostly_male":
            if i not in exp_dict.keys():
                continue
            male_sum +=exp_dict[i]
            male_count+=1
        elif gender == "female" or gender == "mostly_female":
            if i not in exp_dict.keys():
                continue
            female_sum += exp_dict[i]
            female_count+=1
    print(k,(male_sum/male_count)/(female_sum/female_count))
    results["avg_publishing_ratio"]["vm"][k] =( male_sum/male_count)/(female_sum/female_count)

for k,v in seOrg2Exp.items():
    male_sum=0
    female_sum = 0
    male_count=0
    female_count=0
    for i in v:
        gender=mainlist[i]["gender"]
        if gender == "male" or gender == "mostly_male":
            if i not in exp_dict.keys():
                continue
            male_sum +=exp_dict[i]
            male_count+=1
        elif gender == "female" or gender == "mostly_female":
            if i not in exp_dict.keys():
                continue
            female_sum += exp_dict[i]
            female_count+=1
    print(k,(male_sum/male_count)/(female_sum/female_count))
    results["avg_publishing_ratio"]["se"][k] =( male_sum/male_count)/(female_sum/female_count)

#------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------
#                   Analysing TFIDF and Doc2vec models for identifying gender bias
#------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------


nlp = spacy.load('en_core_web_lg')
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

import json
d = gender.Detector()
if __name__ == "__main__":
    model = load_model('doc2vec_roag.model')
    print("-------------------------------Tf Idf--------------------- ")

    #------------------  TF-IDF:  AHSS gender bias identification--------------------------
    with open('ahss_gender_queries.txt') as f:
        data = json.load(f)
    ahss_acc={}
    ahss={}
    total_male_sum=0
    total_female_sum=0
    for k,v in data.items():
        count = 0
        male_sum = 0
        female_sum=0
        sum=0
        total=0
        for a,b in v.items():
            for g,h in b.items():
                text = h["short_query"]
                tf_idf = more_like_this(text, topn=20)
                docs=0
                weights= [ 512/1023,256/1023,128/1023,64/1023,32/1023,16/1023,8/1023,4/1023,2/1023,1/1023 ]
                weighted_female_faction = 0
                weighted_male_faction =0
                acc=0
                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"] )>0:
                        male = 0
                        female = 0
                        if g== document["document_id"]:
                            acc=1
                        for i in document["source"]["names"] :
                            name = i["name"]
                            firstName = name.split(" ")[0]
                            gender = d.get_gender(firstName)
                            if gender == "male" or gender == "mostly_male" :
                                male+=1
                            elif gender == "female" or gender=="mostly_female":
                                female+=1
                        if male +female != 0:
                            female_fraction = female/(male+female)
                            male_fraction = male / (male + female)
                        else :
                            female_fraction=0
                            male_fraction=0
                        weighted_male_faction += male_fraction * weights[docs]
                        weighted_female_faction += female_fraction * weights[docs]
                        docs += 1

                    if docs == 10:
                        break

                if acc==1:
                    sum+=1
                total += 1
                female_sum +=weighted_female_faction
                male_sum += weighted_male_faction
                count+=1

        ahss_acc[k]=sum/total
        ahss[k]=  {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio":male_sum/female_sum}
        total_male_sum+=male_sum
        total_female_sum += female_sum

    for k,v in ahss.items():
        print(format(v["ratio"],".3f"))
        results["tfIdf_MF_ratio"]["ahss"][k]=v

    # print("AHSS MF ratio", total_male_sum/total_female_sum)
    # a=0
    # b=0
    # print()
    # print("______________________ AHSS ACCURACY_________________________________________")
    # for k, v in ahss_acc.items():
    #     print(v)
    #     a+=v
    #     b+=1
    # print("Average Accuracy ", a/b)

    # ------------------  TF-IDF:  VM gender bias identification--------------------------
    with open('vm_gender_queries.txt') as f:
        data = json.load(f)
    vm_acc = {}
    vm = {}
    total_male_sum = 0
    total_female_sum = 0
    for k, v in data.items():
        count = 0
        male_sum = 0
        female_sum = 0
        sum = 0
        total = 0
        for a, b in v.items():
            for g, h in b.items():
                text = h["short_query"]
                tf_idf = more_like_this(text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_female_faction = 0
                weighted_male_faction = 0
                acc = 0
                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        male = 0
                        female = 0
                        if g == document["document_id"]:
                            acc = 1
                        for i in document["source"]["names"]:
                            name = i["name"]
                            firstName = name.split(" ")[0]
                            gender = d.get_gender(firstName)
                            if gender == "male" or gender == "mostly_male":
                                male += 1
                            elif gender == "female" or gender == "mostly_female":
                                female += 1
                        if male + female != 0:
                            female_fraction = female / (male + female)
                            male_fraction = male / (male + female)
                        else:
                            female_fraction = 0
                            male_fraction = 0
                        weighted_male_faction += male_fraction * weights[docs]
                        weighted_female_faction += female_fraction * weights[docs]
                        docs += 1

                    if docs == 10:
                        break

                if acc == 1:
                    sum += 1
                total += 1
                female_sum += weighted_female_faction
                male_sum += weighted_male_faction
                count += 1

        vm_acc[k] = sum / total
        vm[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": male_sum / female_sum}
        total_male_sum += male_sum
        total_female_sum += female_sum

    for k,v in vm.items():
        print(format(v["ratio"],".3f"))
        results["tfIdf_MF_ratio"]["vm"][k] = v

    # print("vm MF ratio", total_male_sum/total_female_sum)
    # a = 0
    # b = 0
    # print()
    # print("______________________ vm ACCURACY_________________________________________")
    # for k, v in vm_acc.items():
    #     print(v)
    #     a += v
    #     b += 1
    # print("Average Accuracy ", a / b)

    # ------------------  TF-IDF:  SE gender bias identification--------------------------
    with open('se_gender_queries.txt') as f:
        data = json.load(f)
    se_acc = {}
    se = {}
    total_male_sum = 0
    total_female_sum = 0
    for k, v in data.items():
        count = 0
        male_sum = 0
        female_sum = 0
        sum = 0
        total = 0
        for a, b in v.items():
            for g, h in b.items():
                text = h["short_query"]
                tf_idf = more_like_this(text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_female_faction = 0
                weighted_male_faction = 0
                acc = 0
                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        male = 0
                        female = 0
                        if g == document["document_id"]:
                            acc = 1
                        for i in document["source"]["names"]:
                            name = i["name"]
                            firstName = name.split(" ")[0]
                            gender = d.get_gender(firstName)
                            if gender == "male" or gender == "mostly_male":
                                male += 1
                            elif gender == "female" or gender == "mostly_female":
                                female += 1
                        if male + female != 0:
                            female_fraction = female / (male + female)
                            male_fraction = male / (male + female)
                        else:
                            female_fraction = 0
                            male_fraction = 0
                        weighted_male_faction += male_fraction * weights[docs]
                        weighted_female_faction += female_fraction * weights[docs]
                        docs += 1

                    if docs == 10:
                        break

                if acc == 1:
                    sum += 1
                total += 1
                female_sum += weighted_female_faction
                male_sum += weighted_male_faction
                count += 1

        se_acc[k] = sum / total
        se[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": male_sum / female_sum}
        total_male_sum += male_sum
        total_female_sum += female_sum

    for k,v in se.items():
        print(k,format(v["ratio"],".3f"))
        results["tfIdf_MF_ratio"]["se"][k] = v

    # print("se MF ratio", total_male_sum/total_female_sum)
    # a = 0
    # b = 0
    # print()
    # print("______________________ se ACCURACY_________________________________________")
    # for k, v in se_acc.items():
    #     print(v)
    #     a += v
    #     b += 1
    # print("Average Accuracy ", a / b)
    # print()
    print("---------------------------doc2vec-----------------------------------")

    # ------------------  Doc2vec:  AHSS gender bias identification--------------------------
    with open('ahss_gender_queries.txt') as f:
        data = json.load(f)
    ahss_acc={}
    ahss={}
    total_male_sum=0
    total_female_sum=0
    for k,v in data.items():
        count = 0
        male_sum = 0
        female_sum=0
        sum=0
        total=0
        for a,b in v.items():
            for g,h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs=0
                weights= [ 512/1023,256/1023,128/1023,64/1023,32/1023,16/1023,8/1023,4/1023,2/1023,1/1023 ]
                weighted_female_faction = 0
                weighted_male_faction =0
                acc=0
                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"] )>0:
                        male = 0
                        female = 0
                        if g== document["document_id"]:
                            acc=1
                        for i in document["source"]["names"] :
                            name = i["name"]
                            firstName = name.split(" ")[0]
                            gender = d.get_gender(firstName)
                            if gender == "male" or gender == "mostly_male" :
                                male+=1
                            elif gender == "female" or gender=="mostly_female":
                                female+=1
                        if male +female != 0:
                            female_fraction = female/(male+female)
                            male_fraction = male / (male + female)
                        else :
                            female_fraction=0
                            male_fraction=0
                        weighted_male_faction += male_fraction * weights[docs]
                        weighted_female_faction += female_fraction * weights[docs]
                        docs += 1

                    if docs == 10:
                        break

                if acc==1:
                    sum+=1
                total += 1
                female_sum +=weighted_female_faction
                male_sum += weighted_male_faction
                count+=1

        ahss_acc[k]=sum/total
        ahss[k]=  {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio":male_sum/female_sum}
        total_male_sum+=male_sum
        total_female_sum += female_sum

    for k,v in ahss.items():
        print(k, format(v["ratio"],".3f"))
        results["doc2vec_MF_ratio"]["ahss"][k] = v

    # a=0
    # b=0
    # print()
    # print("______________________ AHSS ACCURACY_________________________________________")
    # for k, v in ahss_acc.items():
    #     print(v)
    #     a+=v
    #     b+=1
    # print("Average Accuracy ", a/b)

    # ------------------  Doc2vec:  VM gender bias identification--------------------------
    with open('vm_gender_queries.txt') as f:
        data = json.load(f)
    vm_acc = {}
    vm = {}
    total_male_sum = 0
    total_female_sum = 0
    for k, v in data.items():
        count = 0
        male_sum = 0
        female_sum = 0
        sum = 0
        total = 0
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_female_faction = 0
                weighted_male_faction = 0
                acc = 0
                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        male = 0
                        female = 0
                        if g == document["document_id"]:
                            acc = 1
                        for i in document["source"]["names"]:
                            name = i["name"]
                            firstName = name.split(" ")[0]
                            gender = d.get_gender(firstName)
                            if gender == "male" or gender == "mostly_male":
                                male += 1
                            elif gender == "female" or gender == "mostly_female":
                                female += 1
                        if male + female != 0:
                            female_fraction = female / (male + female)
                            male_fraction = male / (male + female)
                        else:
                            female_fraction = 0
                            male_fraction = 0
                        weighted_male_faction += male_fraction * weights[docs]
                        weighted_female_faction += female_fraction * weights[docs]
                        docs += 1

                    if docs == 10:
                        break

                if acc == 1:
                    sum += 1
                total += 1
                female_sum += weighted_female_faction
                male_sum += weighted_male_faction
                count += 1

        vm_acc[k] = sum / total
        vm[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": male_sum / female_sum}
        total_male_sum += male_sum
        total_female_sum += female_sum

    for k,v in vm.items():
        print(k,format(v["ratio"],".3f"))
        results["doc2vec_MF_ratio"]["vm"][k] = v

    # a = 0
    # b = 0
    # print()
    # print("______________________ vm ACCURACY_________________________________________")
    # for k, v in vm_acc.items():
    #     print(v)
    #     a += v
    #     b += 1
    # print("Average Accuracy ", a / b)

    # ------------------  Doc2vec:  SE gender bias identification--------------------------
    with open('se_gender_queries.txt') as f:
        data = json.load(f)
    se_acc = {}
    se = {}
    total_male_sum = 0
    total_female_sum = 0
    for k, v in data.items():
        count = 0
        male_sum = 0
        female_sum = 0
        sum = 0
        total = 0
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_female_faction = 0
                weighted_male_faction = 0
                acc = 0
                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        male = 0
                        female = 0
                        if g == document["document_id"]:
                            acc = 1
                        for i in document["source"]["names"]:
                            name = i["name"]
                            firstName = name.split(" ")[0]
                            gender = d.get_gender(firstName)
                            if gender == "male" or gender == "mostly_male":
                                male += 1
                            elif gender == "female" or gender == "mostly_female":
                                female += 1
                        if male + female != 0:
                            female_fraction = female / (male + female)
                            male_fraction = male / (male + female)
                        else:
                            female_fraction = 0
                            male_fraction = 0
                        weighted_male_faction += male_fraction * weights[docs]
                        weighted_female_faction += female_fraction * weights[docs]
                        docs += 1

                    if docs == 10:
                        break

                if acc == 1:
                    sum += 1
                total += 1
                female_sum += weighted_female_faction
                male_sum += weighted_male_faction
                count += 1

        se_acc[k] = sum / total
        se[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": male_sum / female_sum}
        total_male_sum += male_sum
        total_female_sum += female_sum

    for k,v in se.items():
        print(k,format(v["ratio"],".3f"))
        results["doc2vec_MF_ratio"]["se"][k] = v
    # a = 0
    # b = 0
    # print()
    # print("______________________ se ACCURACY_________________________________________")
    # for k, v in se_acc.items():
    #     print(v)
    #     a += v
    #     b += 1
    # print("Average Accuracy ", a / b)

    with open('gender_bias_results.json', 'w') as json_file:
        json.dump(results, json_file,indent=4)

