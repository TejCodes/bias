import json
import os
import re

import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 

import multiprocessing

from doc2vec_prep import stem_text

# Init the Doc2Vec model
hyperparams  = {
    'vector_size': 300,
    'min_count': 1,
    'epochs': 100,
    'window': 15,
    'negative': 5, 
    'sampling_threshold': 1e-5, 
    'workers': multiprocessing.cpu_count(), 
    'dm': 0
}

def create_stem_tagged_document(publications, projects, documents_file):
    train_data = []
    documents = {}
    for pub_id, publication in publications:
        text = publication['abstract'] + publication['title']
        words = stem_text(text)
        documents[pub_id]={}
        documents[pub_id]['title'] = publication['title']
        documents[pub_id]['people']= publication['authors']
        documents[pub_id]['type'] = 'paper'
        train_data.append(TaggedDocument(words=words, tags=[pub_id]))
    for proj_id, project in projects:
        text = project['title'] + project['description']
        words = stem_text(text)
        documents[proj_id]={}
        documents[proj_id]['title'] = project['title']
        documents[proj_id]['people']= project['people']
        documents[proj_id]['type'] = 'project'
        train_data.append(TaggedDocument(words=words, tags=[proj_id]))

    with open(documents_file, 'w') as f:
        docs = json.dump(documents, f, indent=4)    
    return train_data

def read_input(filename, type):
    with open(filename) as f:
        docs = json.load(f)
    print(f'Loaded {len(docs)} {type}')
    return docs

if __name__ == "__main__":
    my_path = os.path.dirname(__file__)
    publications = read_input(os.path.join(my_path, 'epcc_publications.json'), 'publications')
    projects = read_input(os.path.join(my_path, 'epcc_projects.json'), 'projects')
    docs_with_abstract = filter(lambda p: p[1]['abstract'] is not None, publications.items())
    docs_with_description = filter(lambda p: p[1]['description'] is not None, projects.items())
    documents_file = os.path.join(my_path, 'UoE_documents.json')
    train_data = create_stem_tagged_document(docs_with_abstract, docs_with_description, documents_file)

    # Create the model
    print('Creating the model')
    model = Doc2Vec(**hyperparams)
    
    # Build the vocabulary
    model.build_vocab(train_data)

    # Train the Doc2Vec model
    model.train(train_data, total_examples=model.corpus_count, epochs=model.epochs)

    # # Save the model
    model.save(os.path.join(my_path, 'doc2vec.model'))
    print(f'Saved model to {os.path.join(my_path, "doc2vec.model")}')

