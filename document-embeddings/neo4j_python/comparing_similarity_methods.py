import glob
import json
import os
import json
import re
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from collections import defaultdict
from scipy import spatial
import collections
import spacy
import MySQLdb
nlp = spacy.load('en_core_web_lg')

import configparser
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MoreLikeThis


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


def get_searches(c, test_id):
    query=("SELECT * FROM opportunity_match_search where id = {}".format(test_id))
    c.execute(query)
    row = c.fetchone()
    all_searches_by_user = defaultdict(list)
    while row is not None:
        s = {
            'id': row[0],
            'name': row[1],
            'text': row[2],
            'timestamp': row[3].isoformat(),
        }
        all_searches_by_user[row[4]].append(s)
        row = c.fetchone()

    for i in all_searches_by_user:
        return all_searches_by_user[i][0]



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
    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.mysql_env')
    config.read(configfile)

    db = MySQLdb.connect(
            user=config['mysql']['USERNAME'],
            passwd=config['mysql']['PASSWORD'],
            db=config['mysql']['DATABASE'])

    c = db.cursor()
    es = Elasticsearch()

    model = Doc2Vec.load(os.path.join("./models/", 'doc2vec_neo4j_v1.model'), mmap='r')
    print("Len of the model %s" % len(model.docvecs))
    doc_tags=list(model.docvecs.doctags)
    #print(doc_tags[0:10])
    # Config

    for search_id in range(20):
        doc_test = get_searches(c, str(search_id))
        if doc_test:
            text = doc_test['name'] + doc_test['text']
            c_text = clean_text(text)
            print("!!! --> Search %s, Name: %s, Text: %s" %(search_id, doc_test['name'], doc_test['text']))
            print("-- Gensim --")
            vector = model.infer_vector(c_text, epochs=100)
            simdocs_gen = model.docvecs.most_similar([vector], topn=len(model.docvecs))
            rank_gen = [docid for docid, sim in simdocs_gen]
            rank_i = 0
            for rank_id in rank_gen[0:10]:
                doc_es = get_document(rank_id)
                print("Document %s, Similar to %s with title %s, position %s, score %s" %(search_id, rank_id, doc_es["title"], rank_i, simdocs_gen[rank_i][1]))
                rank_i += 1
                
            print("-- ES --")
            simdocs_es=similar_es_documents(c_text)
            rank_es = [(d.document_id, d.meta.score) for d in simdocs_es]
            rank_i_es = 0
            for rank_d in rank_es[0:10]:
                doc_es = get_document(rank_d[0])
                print("Document %s, Similar to %s with title %s, position %s, score %s" %(search_id, rank_d[0], doc_es["title"], rank_i_es, rank_d[1]))
                rank_i_es += 1
                






           


