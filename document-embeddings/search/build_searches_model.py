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
# Init the Doc2Vec model
hyperparams  = { 'dm':1,    
                 'vector_size':300,
                 'window':5,
                 'alpha':0.025,
                 'min_alpha':0.00025,
                 'min_count':2,
                 'workers':2}
min_length = 2




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




def generate_searches_documents(c, clean_func=clean_text, min_length=2):
    # modify this to retrieve only public searches, or include private
    shared_only = False # all searches for now
    gen_docs = 0
    c.execute('SELECT * FROM opportunity_match_search')
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

    all_searches = []
    for user_id, searches in all_searches_by_user.items():
        c.execute(f'''
        SELECT uuid, auth_user.id, first_name, last_name
        FROM opportunity_match_settings
        RIGHT OUTER JOIN auth_user
        ON user_id=auth_user.id
        WHERE auth_user.id={user_id}
        ''')
        settings = c.fetchone()
        for s in searches:
            s['person'] = {
                'id': settings[1],
                'name': f'{settings[2]} {settings[3]}',
            }
            if settings[0]:
                s['person']['uuid'] = settings[0]
            all_searches.append(s)

    for resout_node in all_searches:
        resout_id = resout_node["id"]
        if resout_node["text"] != "":
           text = resout_node["text"] + resout_node["name"]
           words = clean_func(text)
           if len(words) >= min_length:
               gen_docs += 1
               yield TaggedDocument(words=words, tags=[resout_node["id"]])

    print(f'Generated {gen_docs} documents')


if __name__ == "__main__":
    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    db = MySQLdb.connect(
            user=config['mysql']['USERNAME'],
            passwd=config['mysql']['PASSWORD'],
            db=config['mysql']['DATABASE'])


    c = db.cursor()
    train_documents = list(tqdm(generate_searches_documents(c, clean_text, min_length=2)))
    print(f'Created {len(train_documents)} tagged documents.')
    model = Doc2Vec(**hyperparams)
    print('Build vocabulary')
    model.build_vocab(train_documents)
    for epoch in range(100):
        print(f'Train model: epoch={epoch}')
        model.train(train_documents, total_examples=model.corpus_count, epochs=1)
        model.alpha -= 0.0002
        model.min_alpha = model.alpha

    # Save the model
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'doc2vec_search.model')
    model.save(model_path)
    print(f'Saved model to {model_path}')
    
    #### Quick test - taking the text of search number 72
    text="Data science provides many opportunities to improve private and public life, and it has enjoyed significant investment in the UK, EU and elsewhere. Discovering patterns and structures in large troves of data in an automated manner - that is, machine learning - is a core component of data science. Machine learning currently drives applications in computational biology, natural language processing and robotics. However, such a highly positive impact is coupled to a significant challenge: when can we convincingly deploy these methods in our workplace? For example:\r\n\r\n(a) how can we elicit intuitive and reasonable "
    vector = model.infer_vector(clean_text(text), epochs=100)
    simdocs = model.docvecs.most_similar([vector], topn=len(model.docvecs))
    print(simdocs)
