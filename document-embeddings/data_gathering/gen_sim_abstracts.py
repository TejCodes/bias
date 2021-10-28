import json
import os   

import gensim
import nltk
from nltk.corpus import stopwords

import opportunities

def tokenize_text(text):
    tokens = []
    for sent in nltk.sent_tokenize(text):
        for word in nltk.word_tokenize(sent):
            if len(word) < 2:
                continue
            tokens.append(word.lower())
    return tokens

def create_tagged_document(publication):
    tokens = tokenize_text(publication['abstract'])
    tokens += tokenize_text(publication['title'])
    return gensim.models.doc2vec.TaggedDocument(tokens, [publication['id']])

def read_input(filename):
    with open(filename) as f:
        publications = json.load(f)
    print(f'Loaded {len(publications)} publications')
    return publications

if __name__ == "__main__":

    publications = read_input(os.path.join(os.path.dirname(__file__), 'epcc_publications.json'))
    docs_with_abstract = filter(lambda p: p['abstract'] is not None, publications)
    train_data = list(map(create_tagged_document, docs_with_abstract))
    documents = {p['id']: p for p in publications}
    # print(train_data[:1])

    # Init the Doc2Vec model
    model = gensim.models.doc2vec.Doc2Vec(vector_size=10, min_count=2, epochs=40)

    # Build the vocabulary
    model.build_vocab(train_data)

    # Train the Doc2Vec model
    model.train(train_data, total_examples=model.corpus_count, epochs=model.epochs)

    contents = opportunities.get_text_from_url('https://epsrc.ukri.org/funding/calls/newapproachestodatascience/')
    vector = model.infer_vector(tokenize_text(contents))
    simdocs = model.docvecs.most_similar(positive=[vector])
    matching_authors = set()
    for doc in simdocs:
        publication = documents[doc[0]]
        print(f'Similarity: {doc[1]}')
        print(f'Authors: {publication["authors"]}')
        print(f'Abstract: {publication["abstract"]}')
        matching_authors = matching_authors.union(set(publication['authors']))

    print('Matching experts:')
    for a in matching_authors:
        print(f' - {a}')

