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


def norm_score(score, window):
    # Normalization ---> (actual_score - min_score) / (max_score - min_score)
    max_score=max(score[0:window])
    min_score=min(score[0:window])
    n_score = max_score - min_score
    new_score=[]
    for sc in score[0:window]:
        d_score= sc - min_score
        new_score.append(d_score/n_score)
    return new_score



def similar_es_documents(text, window):
    s = Search().using(es).query(MoreLikeThis(like=text, fields=['abstract', 'tech_abstract'], min_term_freq=1, max_query_terms=12))
    response = s.execute()
    for hit in s[0:window]:
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
    doc_tags=list(model.docvecs.doctags)

    for search_id in range(80):
        doc_test = get_searches(c, str(search_id))
        if doc_test:
            text = doc_test['name'] + doc_test['text']
            c_text = clean_text(text)
            print("!!! --> Search %s, Name: %s, Text: %s" %(search_id, doc_test['name'], doc_test['text']))
            vector = model.infer_vector(c_text, epochs=100)
            simdocs_gen = model.docvecs.most_similar([vector], topn=len(model.docvecs))
            rank_gen = [docid for docid, sim in simdocs_gen]
            score_gen = [sim for docid, sim in simdocs_gen]

            max_wind_size=10000
            
            simdocs_es=similar_es_documents(c_text, max_wind_size)
            rank_es = [(d.document_id, d.meta.score/100) for d in simdocs_es]
            score_es = [ sim for docid, sim in rank_es]


            norm_window=len(score_es)
            norm_score_gen=norm_score(score_gen, norm_window)
            norm_score_es=norm_score(score_es, norm_window)

            combine_score ={}

            gen_index=0
            for rank_id_gen in rank_gen[0:norm_window]:
                es_index = 0
                for rank_d_es in rank_es:
                    if rank_d_es[0] == rank_id_gen :
                         score_comb=norm_score_gen[gen_index] * norm_score_es[es_index]
                         combine_score[rank_id_gen]= score_comb
                         break
                    else:
                        es_index += 1

                if rank_id_gen not in combine_score:
                    combine_score[rank_id_gen]=norm_score_gen[gen_index]
                gen_index += 1

            es_index =0
            for rank_d_es in rank_es:
                if rank_d_es[0] not in combine_score:
                    gen_index = 0
                    for rank_id_gen in rank_gen[0:norm_window]:
                        if rank_id_gen == rank_d_es[0]:
                            score_comb=norm_score_gen[gen_index] * norm_score_es[es_index]
                            combine_score[rank_id_gen]= score_comb
                            break
                        else:
                            gen_index += 1
                    if rank_d_es[0] not in combine_score:
                        combine_score[rank_d_es[0]]=norm_score_es[es_index]
                es_index += 1


            sorted_score={k: v for k, v in sorted(combine_score.items(), key=lambda item: item[1])}
            rank_i = 0
            
            comb_sorted_score = []
            for key, value in sorted_score.items():
                temp = (key,value)
                comb_sorted_score.insert(0,temp)

            rank_i = 0
            window_results=15
            for d_index in comb_sorted_score[0:window_results]:
                doc_es = get_document(d_index[0])
                print("Search %s, Similar to %s with title %s, position in the ranking %s, with score %s" %(search_id, d_index[0], doc_es["title"], rank_i, d_index[1]))
                rank_i += 1




                






           


