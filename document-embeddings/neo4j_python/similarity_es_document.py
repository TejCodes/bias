import glob
import json
import os
import json
import re
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from scipy import spatial
import collections
import spacy
nlp = spacy.load('en_core_web_lg')

import configparser
from elasticsearch import Elasticsearch
from elasticsearch_dsl.query import MoreLikeThis
from elasticsearch_dsl import Search


def similar_es_documents(text):
    s = Search().using(es).query(MoreLikeThis(like=text, fields=['abstract', 'tech_abstract'], min_term_freq=1, max_query_terms=12))
    response = s.execute()
    for hit in s[0:100]:
        yield hit

def get_document(doc_id):
    s = Search().using(es).query("match", document_id=doc_id)
    response = s.execute()
    if response.hits.total.value > 0:
        return response.to_dict()['hits']['hits'][0]['_source']
    return None


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
        #txt = [token.lemma_ for token in sentence if not token.is_punct]
        txt = [token.lemma_ for token in sentence if not token.is_punct and not token.is_stop]
        all_texts.append(txt)
    return [val for sublist in all_texts for val in sublist]




if __name__ == "__main__":

    es = Elasticsearch()

    model = Doc2Vec.load(os.path.join("./models/", 'doc2vec_neo4j_v1.model'), mmap='r')
    print("Len of the model %s" % len(model.docvecs))
    doc_tags=list(model.docvecs.doctags)
    # Config
    total_zero=0
    for test_id in doc_tags[0:100]:
        doc_test = get_document(test_id)
        text = doc_test['title'] + doc_test['abstract']
        if doc_test :
            c_text = clean_text(text)
            simdocs_es=similar_es_documents(c_text)
            rank = [d.document_id for d in simdocs_es]
            if rank.index(test_id) == 0:
                total_zero+=1
    print("Total first position %s" %total_zero)






