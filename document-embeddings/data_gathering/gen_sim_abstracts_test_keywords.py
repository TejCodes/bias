import json
import os   

import gensim
import re

from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from gensim.utils import simple_preprocess

import multiprocessing

import opportunities

# Init the Doc2Vec model
hyperparams  = {
    'vector_size': 300,
    'min_count': 1,
    'epochs': 100,
    'window': 15,
    'negative': 5, 
    'sampling_threshold': 1e-5, 
    'cores': multiprocessing.cpu_count(), 
    'dm': 0
}

def stem_text(text):
    p = PorterStemmer()
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE) # remove email
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE) # remove web addresses
    text = re.sub("\'", "", text) # remove single quotes
    text = remove_stopwords(text)
    text = p.stem_sentence(text)
    return simple_preprocess(text, deacc=True)


def create_stem_tagged_document(publication):
    text = publication['keywords']
    words = stem_text(text)
    return TaggedDocument(words=words, tags=[publication['id']])

def read_input(filename):
    with open(filename) as f:
        publications = json.load(f)
    print(f'Loaded {len(publications)} publications')
    return publications

if __name__ == "__main__":

    publications = read_input(os.path.join(os.path.dirname(__file__), 'epcc_publications.json'))
    docs_with_keywords = []
    for p in publications:
        try:
            if p['keywords']:
                docs_with_keywords.append(p)
        except:
            pass

    train_data=[]
    for i in docs_with_keywords:
        train_data.append(create_stem_tagged_document(i))

    # Create the model
    model = Doc2Vec(vector_size=hyperparams['vector_size'], window=hyperparams['window'], min_count=hyperparams['min_count'], sampling_threshold = hyperparams['sampling_threshold'], negative=hyperparams['negative'], workers=hyperparams['cores'], dm=hyperparams['dm'], epochs=hyperparams['epochs'])
    
    # Build the vocabulary
    model.build_vocab(train_data)
    # Train the Doc2Vec model
    
    model.train(train_data, total_examples=model.corpus_count, epochs=model.epochs)
    # Saving Full Model
    
    model.save('keywords.doc2vec')

