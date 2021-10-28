import configparser
import os, re
from tqdm import tqdm
from collections import defaultdict
import configparser
import json
import os
import MySQLdb


import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
import multiprocessing


import glob
import json
import os
import json
from scipy import spatial
import collections
import spacy, re

import spacy
nlp = spacy.load('en_core_web_lg')

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
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    db = MySQLdb.connect(
            user=config['mysql']['USERNAME'],
            passwd=config['mysql']['PASSWORD'],
            db=config['mysql']['DATABASE'])

    c = db.cursor()
    model = Doc2Vec.load(os.path.join("./", 'doc2vec_search.model'), mmap='r')
    print("Len of the model %s" % len(model.docvecs))
    # Config
    position=[]
    for test_id in range(100):
        doc_test = get_searches(c, str(test_id))
        if doc_test:
            #print("Doc test is %s" % doc_test)
            text = doc_test['name'] + doc_test['text']
            vector = model.infer_vector(clean_text(text), epochs=100)
            simdocs = model.docvecs.most_similar([vector], topn=len(model.docvecs))
            print("---> Test_id %s - %s" %(test_id, simdocs))
            rank = [docid for docid, sim in simdocs]
            position.append(rank.index(test_id))
            print("The search %s, has been found as the most similar document at position %s" %(test_id, rank.index(test_id)))
