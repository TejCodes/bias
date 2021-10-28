import json
import numpy as np
import os   
import pandas as pd
import gensim
import re
from gensim.models import KeyedVectors

from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from gensim.utils import simple_preprocess
from gensim.models import KeyedVectors 

import opportunities

def stem_text(text):
    p = PorterStemmer()
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE) # remove email
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE) # remove web addresses
    text = re.sub("\'", "", text) # remove single quotes
    text = remove_stopwords(text)
    text = p.stem_sentence(text)
    return simple_preprocess(text, deacc=True)


def create_stem_tagged_document(publication):
    text = publication['abstract']
    text += publication['title']
    words = stem_text(text)
    return TaggedDocument(words=words, tags=[publication['id']])


def read_input(filename):
    with open(filename) as f:
        publications = json.load(f)
    print(f'Loaded {len(publications)} publications')
    return publications

if __name__ == "__main__":
    
    publications = read_input(os.path.join(os.path.dirname(__file__), 'epcc_publications.json'))
    docs_with_abstract = filter(lambda p: p['abstract'] is not None, publications)
    train_data = list(map(create_stem_tagged_document, docs_with_abstract))
    documents = {p['id']: p for p in publications}

    #Load the full Model
    model= Doc2Vec.load('doc2vec.model', mmap='r')
    
    #Load the KV Model
    #model = KeyedVectors.load_word2vec_format('word2vec.kv', binary=True)
    #model.syn0norm = model.syn0  # prevent recalc of normed vectors
 
    ### Testing with an abstract (defoe)
    contents = opportunities.get_text_from_url('https://www.research.ed.ac.uk/portal/en/publications/defoe-a-sparkbased-toolbox-for-analysing-digital-historical-textual-data(a9682a06-d159-4d00-9f92-f9a27f0bb385).html')
    
    vector = model.infer_vector(stem_text(contents))
    simdocs = model.docvecs.most_similar(positive=[vector])
    
    matching_authors = []

    for doc in simdocs:
        publication = documents[doc[0]]
        print(f'Similarity: {doc[1]}')
        print(f'Authors: {publication["authors"]}')
        print(f'Abstract: {publication["abstract"]}')
        matching_authors.append(publication['authors'])

    print('Total experts (By order):')
    matching_experts = []
    for l_a in matching_authors:
        print(f' - {l_a}')
        for a in l_a:
            if a not in matching_experts:
                matching_experts.append(a)

    print('Recommended experts (By order):')
    for a in matching_experts:
        print(f' - {a}')
   
    
