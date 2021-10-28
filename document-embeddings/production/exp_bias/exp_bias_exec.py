import os
import re
from gensim.models.doc2vec import Doc2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from collections import defaultdict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MoreLikeThis
import spacy
import json

with open('../common_files/constants.json') as f:
    constants = json.load(f)


nlp = spacy.load('en_core_web_lg')
# model = Doc2Vec.load(os.path.join(settings.BASE_DIR, 'models/doc2vec.model'), mmap='r')
MODEL_PATH = "../"
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

def add(a,b):
    c=[]
    for i in range(len(a)):
        c.append(a[i]+b[i])
    return c

def mult(a,b):
    c=[]
    for i in range(len(a)):
        c.append(a[i]*b)
    return c

import json
if __name__ == "__main__":
    model = load_model('doc2vec_roag.model')

    with open('exp_bias_results.json') as fp:
        results = json.load(fp)

    with open('../common_files/exp_dict.json') as fp:
        exp_dict = json.load(fp)

    with open('ahss_exp_queries.txt') as f:
        data = json.load(f)

    print("-------------------------------Tf Idf--------------------- ")

    ahss={}
    for k,v in data.items():
        count = 0
        sum = [0.0, 0.0, 0.0, 0.0]
        for a,b in v.items():
            for g,h in b.items():
                text = h["short_query"]
                tf_idf = more_like_this(text, topn=20)
                docs=0
                weights= [ 512/1023,256/1023,128/1023,64/1023,32/1023,16/1023,8/1023,4/1023,2/1023,1/1023 ]
                weighted_distr = [0.0, 0.0, 0.0, 0.0]

                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"] )>0:
                        a = 0
                        b = 0
                        c = 0
                        d = 0
                        for i in document["source"]["names"] :
                            v = exp_dict[i["uuid"]]
                            if v < 7:
                                a += 1
                            if v >= 7 and v < 30:  # moderate
                                b += 1
                            if v >= 30 and v < 100:  # experienced
                                c += 1
                            if v >= 100:  # very experienced
                                d += 1
                        t=a+b+c+d
                        distr=[a*weights[docs]/t,b*weights[docs]/t,c*weights[docs]/t,d*weights[docs]/t]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        ahss[k]=  {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio":sum}


    results["tfIdf"]={}
    results["doc2vec"] = {}
    results["tfIdf"]["ahss"]=ahss
    for k,v in ahss.items():
        print(v["ratio"])

    with open('vm_exp_queries.txt') as f:
        data = json.load(f)

    vm = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0, 0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["short_query"]
                tf_idf = more_like_this(text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0, 0.0, 0.0]

                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        a = 0
                        b = 0
                        c = 0
                        d = 0
                        for i in document["source"]["names"]:
                            v = exp_dict[i["uuid"]]
                            if v < 7:
                                a += 1
                            if v >= 7 and v < 30:  # moderate
                                b += 1
                            if v >= 30 and v < 100:  # experienced
                                c += 1
                            if v >= 100:  # very experienced
                                d += 1
                        t = a + b + c + d
                        distr = [a * weights[docs] / t, b * weights[docs] / t, c * weights[docs] / t,
                                 d * weights[docs] / t]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        vm[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": sum}
    results["tfIdf"]["vm"] = vm
    for k, v in vm.items():
        print(v["ratio"])

    with open('se_exp_queries.txt') as f:
        data = json.load(f)

    se = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0, 0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["short_query"]
                tf_idf = more_like_this(text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0, 0.0, 0.0]

                for doc_id, rank in tf_idf:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        a = 0
                        b = 0
                        c = 0
                        d = 0
                        for i in document["source"]["names"]:
                            v = exp_dict[i["uuid"]]
                            if v < 7:
                                a += 1
                            if v >= 7 and v < 30:  # moderate
                                b += 1
                            if v >= 30 and v < 100:  # experienced
                                c += 1
                            if v >= 100:  # very experienced
                                d += 1
                        t = a + b + c + d
                        distr = [a * weights[docs] / t, b * weights[docs] / t, c * weights[docs] / t,
                                 d * weights[docs] / t]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        se[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": sum}

    results["tfIdf"]["se"] = se
    for k, v in se.items():
        print(v["ratio"])

    with open('ahss_exp_queries.txt') as f:
        data = json.load(f)


    print()
    print("-------------------------------doc2Vec----------------------- ")
    with open('ahss_exp_queries.txt') as f:
        data = json.load(f)
    ahss = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0, 0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0, 0.0, 0.0]

                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        a = 0
                        b = 0
                        c = 0
                        d = 0
                        for i in document["source"]["names"]:
                            v = exp_dict[i["uuid"]]
                            if v < 7:
                                a += 1
                            if v >= 7 and v < 30:  # moderate
                                b += 1
                            if v >= 30 and v < 100:  # experienced
                                c += 1
                            if v >= 100:  # very experienced
                                d += 1
                        t = a + b + c + d
                        distr = [a * weights[docs] / t, b * weights[docs] / t, c * weights[docs] / t,
                                 d * weights[docs] / t]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        ahss[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": sum}

    results["doc2vec"]["ahss"] = ahss
    for k, v in ahss.items():
        print(v["ratio"])
    with open('vm_exp_queries.txt') as f:
        data = json.load(f)

    vm = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0, 0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0, 0.0, 0.0]

                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        a = 0
                        b = 0
                        c = 0
                        d = 0
                        for i in document["source"]["names"]:
                            v = exp_dict[i["uuid"]]
                            if v < 7:
                                a += 1
                            if v >= 7 and v < 30:  # moderate
                                b += 1
                            if v >= 30 and v < 100:  # experienced
                                c += 1
                            if v >= 100:  # very experienced
                                d += 1
                        t = a + b + c + d
                        distr = [a * weights[docs] / t, b * weights[docs] / t, c * weights[docs] / t,
                                 d * weights[docs] / t]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        vm[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": sum}

    results["doc2vec"]["vm"] = vm
    for k, v in vm.items():
        print(v["ratio"])

    with open('se_exp_queries.txt') as f:
        data = json.load(f)

    se = {}
    for k, v in data.items():
        count = 0
        sum = [0.0, 0.0, 0.0, 0.0]
        for a, b in v.items():
            for g, h in b.items():
                text = h["long_query"]
                cleaned_text = clean_text(text)
                simdocs = most_similar(model, text, topn=20)
                docs = 0
                weights = [512 / 1023, 256 / 1023, 128 / 1023, 64 / 1023, 32 / 1023, 16 / 1023, 8 / 1023, 4 / 1023,
                           2 / 1023, 1 / 1023]
                weighted_distr = [0.0, 0.0, 0.0, 0.0]

                for doc_id, rank in simdocs:
                    document = get_document(doc_id)
                    if len(document["source"]["names"]) > 0:
                        a = 0
                        b = 0
                        c = 0
                        d = 0
                        for i in document["source"]["names"]:
                            v = exp_dict[i["uuid"]]
                            if v < 7:
                                a += 1
                            if v >= 7 and v < 30:  # moderate
                                b += 1
                            if v >= 30 and v < 100:  # experienced
                                c += 1
                            if v >= 100:  # very experienced
                                d += 1
                        t = a + b + c + d
                        distr = [a * weights[docs] / t, b * weights[docs] / t, c * weights[docs] / t,
                                 d * weights[docs] / t]
                        weighted_distr = add(distr, weighted_distr)
                        docs += 1

                    if docs == 10:
                        break
                sum = add(sum, weighted_distr)
                count += 1
        for i in range(len(sum)):
            sum[i] = sum[i] / count

        se[k] = {
            # "mf": male_sum/count, "ff":female_sum/count,
            "ratio": sum}
    results["doc2vec"]["se"] = se
    for k, v in se.items():
        print(v["ratio"])

    with open('exp_bias_results.json', 'w') as json_file:
        json.dump(results, json_file,indent=4)

