import argparse
from collections import defaultdict
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

def create_stem_tagged_document(publications, projects):
    person_data = defaultdict(list)
    for pub_id, publication in publications:
        text = publication['abstract'] + publication['title']
        words = stem_text(text)
        for author in publication['authors']:
            person_data[author['uuid']] = person_data[author['uuid']] + words
    for proj_id, project in projects:
        text = project['title'] + project['description']
        words = stem_text(text)
        for person in project['people']:
            person_data[person['uuid']] = person_data[person['uuid']] + words

    train_data = []
    for person_id, words in person_data.items():
        train_data.append(TaggedDocument(words=words, tags=[person_id]))
    return train_data


def read_input(filename, type):
    with open(filename) as f:
        docs = json.load(f)
    print(f'Loaded {len(docs)} {type}')
    return docs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pub', '--research-outputs', help='Research outputs', required=True)
    parser.add_argument('-proj', '--projects', help='Projects', required=True)
    args = parser.parse_args()

    my_path = os.path.dirname(__file__)
    publications = read_input(os.path.join(my_path, args.research_outputs), 'publications')
    projects = read_input(os.path.join(my_path, args.projects), 'projects')
    docs_with_abstract = filter(lambda p: p[1]['abstract'] != '', publications.items())
    docs_with_description = filter(lambda p: p[1]['description'] != '', projects.items())
    train_data = create_stem_tagged_document(docs_with_abstract, docs_with_description)

    # Create the model
    print('Creating the model')
    model = Doc2Vec(**hyperparams)
    
    # Build the vocabulary
    model.build_vocab(train_data)

    # Train the Doc2Vec model
    model.train(train_data, total_examples=model.corpus_count, epochs=model.epochs)

    # # Save the model
    model_path = os.path.join(my_path, 'doc2vec_v2.model')
    model.save(model_path)
    print(f'Saved model to {model_path}')

