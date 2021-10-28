import json
import os
import re

from gensim.models.doc2vec import Doc2Vec
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess

from collections import defaultdict
import uuid

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MoreLikeThis


import spacy
nlp = spacy.load('en_core_web_lg')

# model = Doc2Vec.load(os.path.join(settings.BASE_DIR, 'models/doc2vec.model'), mmap='r')

MODEL_PATH="./"

es = Elasticsearch([{'host':'192.168.1.236','port':9200}])

def get_document(doc_id):
    s = Search().using(es).index('expertise').query("match", document_id=doc_id)
    response = s.execute()
    if response.hits.total.value > 0:
        return response.to_dict()['hits']['hits'][0]['_source']
    return None

def get_person(person_id):
    response = es.search(index='experts',
        body = {
            "query": {
                "match" : { "uuid": person_id }
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
    return [(k, v) for k,v in results.items()]


def stem_text(text):
    p = PorterStemmer()
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE) # remove email
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE) # remove web addresses
    text = re.sub("\'", "", text) # remove single quotes
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


if __name__ == "__main__":

   model=load_model('doc2vec_roag.model')
   
   text="This work presents defoe, a new scalable and portable digital eScience toolbox that enables historical research. It allows for running text mining queries across large datasets, such as historical newspapers and books in parallel via Apache Spark. It handles queries against collections that comprise several XML schemas and physical representations. The proposed tool has been successfully evaluated using five different large-scale historical text datasets and two HPC environments, as well as on desktops. Results shows that defoe allows researchers to query multiple datasets in parallel from a single command-line interface and in a consistent way, without any HPC environment-specific requirements."

   cleaned_text = clean_text(text)
   # Just going to take the firs 10 -- so topn=10
   simdocs=most_similar(model, text, topn=10)

   print("#### TEST 1 -- Doc2Vec -- Printing the details of the 10 most similar documents using Doc2Vec ")
   for doc_id , rank in simdocs:
       document = get_document(doc_id)
       print("!! Using DocVec --- Document_id: %s - Rank %s - Details:  %s" %(doc_id, rank, document))
       print("---")

   print("#### TEST 2 -- Printing the details of first author from the most similar document found before")
   doc_id=simdocs[0][0]
   document = get_document(doc_id)
   uuid=document['source']['names'][0]['uuid']
   profile=get_person(uuid)
   print("--> The profile of the first person listed in the document is %s - %s" %(uuid, profile))
   print("---")

   print("#### TEST 3 -- More like this -- Priting the details of 10 most similar documents using TF-IDF")
   text="defoe, spark, digital humanities, historians"
   tf_idf=more_like_this(text, topn=10)
   for doc_id , rank in tf_idf:
       document = get_document(doc_id)
       print("!! Using TF-IDF --- Document_id: %s - Rank %s - Details:  %s" %(doc_id, rank, document))
       print("---")
