import json
import os
import re
from tqdm import tqdm

import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
import spacy
nlp = spacy.load('en_core_web_lg')

from django.core.management.base import BaseCommand
from opportunity_match.models import Search


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

def generate_searches_documents(clean_func=clean_text, min_length=2, include_private=False):
    # modify this to retrieve only public searches, or include private
    gen_docs = 0
    all_searches = Search.objects
    if not include_private:
        all_searches = all_searches.filter(shared=True)
    for search in all_searches.all():
        if search.text != "":
           text = search.text + " " + search.name
           words = clean_func(text)
           if len(words) >= min_length:
               gen_docs += 1
               yield TaggedDocument(words=words, tags=[search.id])
    print(f'Generated {gen_docs} documents')

class Command(BaseCommand):
    help = 'Collects the number of times experts appeared in searches'

    def add_arguments(self, parser):
        parser.add_argument('output')
        parser.add_argument('--private', default=False, action='store_true')

    def handle(self, *args, **options):

        train_documents = list(tqdm(generate_searches_documents(
            clean_text, min_length=2, include_private=options['private'])))
        self.stdout.write(f'Created {len(train_documents)} tagged documents.')
        if len(train_documents) == 0:
            self.stdout.write('No input documents - stop.')
            return
        model = Doc2Vec(**hyperparams)
        self.stdout.write('Build vocabulary')
        model.build_vocab(train_documents)
        for epoch in range(100):
            self.stdout.write(f'Train model: epoch={epoch}')
            model.train(train_documents, total_examples=model.corpus_count, epochs=1)
            model.alpha -= 0.0002
            model.min_alpha = model.alpha
        self.stdout.write(f'Trained model on {model.corpus_count} searches')

        # Save the model
        model_path = options['output']
        model.save(model_path)
        self.stdout.write(f'Saved model to {model_path}')
