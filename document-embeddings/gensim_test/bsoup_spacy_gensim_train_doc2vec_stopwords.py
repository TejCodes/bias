import requests
from bs4 import BeautifulSoup

import numpy as np
import re

import gensim
import gensim.corpora as corpora
from gensim.models import LdaModel, LdaMulticore

import spacy
from spacy.lemmatizer import Lemmatizer
from spacy.lang.en.stop_words import STOP_WORDS
import en_core_web_lg

import textacy.keyterms
from pprint import pprint

'''
It does the same as bsoup_spacy_gensim_train_doc2vec.py, but it includes the "cleaning" + "stop words" steps (pipeline), before creating the doc2vec model 
'''

nlp = spacy.load("en")


def extract_text_from_url(url_input, clean_symb=True):

    r = requests.get(url_input)
    
    text = BeautifulSoup(r.text, 'html.parser').get_text()

    # Three regexes below adapted from Blendle cleaner.py
    # https://github.com/blendle/research-summarization/blob/master/enrichers/cleaner.py#L29
    if clean_symb:
        text = re.sub(r"[^A-Za-z0-9(),!.?\'`]", " ", text )
        text = re.sub(r"\'s", " 's ", text )
        text = re.sub(r"\'ve", " 've ", text )
        text = re.sub(r"n\'t", " 't ", text )
        text = re.sub(r"\'re", " 're ", text )
        text = re.sub(r"\'d", " 'd ", text )
        text = re.sub(r"\'ll", " 'll ", text )
        text = re.sub(r",", " ", text )
        text = re.sub(r"\.", " ", text )
        text = re.sub(r"!", " ", text )
        text = re.sub(r"\(", " ( ", text )
        text = re.sub(r"\)", " ) ", text )
        text = re.sub(r"\?", " ", text )
        text = re.sub(r"\s{2,}", " ", text )
        text = re.sub(r'\s+', ' ', text).strip()

    return text

def custom_stop_words():

    #Create a custom stop list
    weekDays = ["Monday", "Tuesday" , "Wednesday" , "Thursday" , "Friday" , "Saturday" , "Sunday"]
    
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "month", "year"]
   
    short_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
    
    univ_words = ["researcher", "staff", "money", "research", "student", "lecturer", "partner", "University", "council", "group",  "UK", "PDF", "organization", "organisation", "team", "career", "host"]

    applic_words = ["application", "guide", "guideline", "award", "outline", "support", "closing", "starting", "date", "project", "submission", "policy", "apply", "submit", "letter", "grant", "applicant", "work", "form", "pay", "travel"]

    website_words = ["login", "sign", "website", "cookie", "username", "new", "wellcome", "member", "help", "password", "contact", "email", "Home"]
   
    budget_words = ["money", "cost", "indirect", "direct", "budget", "funding", "fund", "costing", "equipment"]

    verbs = ["ask", "cover", "provide", "use", "need", "include"]
    
    stop_list = weekDays + months + short_months + univ_words + budget_words + website_words + applic_words + verbs

    # Updates spaCy's default stop words list with my additional words. 
    nlp.Defaults.stop_words.update(stop_list)

    # Iterates over the words in the stop words list and resets the "is_stop" flag.
    for word in STOP_WORDS:
        lexeme = nlp.vocab[word]
        lexeme.is_stop = True

    # Updates spaCy's default stop words list with my additional words. 
    nlp.Defaults.stop_words.update(stop_list)

    # Iterates over the words in the stop words list and resets the "is_stop" flag.
    for word in STOP_WORDS:
        lexeme = nlp.vocab[word]
        lexeme.is_stop = True


def norm_lemmatizer(doc):
    # This takes in a doc of tokens from the NER, filter out NUM and Sym, and lemmatizes them. 
    # Pronouns (like "I" and "you" get lemmatized to '-PRON-', so I'm removing those.
    doc = [token for token in doc if token.pos_ != "NUM" and token.pos_ != "SYM"]
    doc = [token.lemma_ for token in doc if token.lemma_ != '-PRON-']
    doc = u' '.join(doc)
    return nlp.make_doc(doc)
    
def remove_stopwords(doc):
    # This will remove stopwords and punctuation.
    # Use token.text to return strings, which we'll need for Gensim.
    doc = [token.text for token in doc if token.is_stop != True and token.is_punct != True]
    return doc

def create_tagged_document(list_of_list_of_words):
    for i, list_of_words in enumerate(list_of_list_of_words):
        yield gensim.models.doc2vec.TaggedDocument(list_of_words, [i])


if __name__ == '__main__':
   
   list_urls=[]
   list_urls.append("https://www.ukri.org/news/decarbonising-heating-and-cooling-for-net-zero-survey-of-needs/")
   list_urls.append("https://www.events.ed.ac.uk/index.cfm?event=showEventDetails&scheduleId=37896&start=&eventStart=0&eventProviderId=21")
   list_urls.append("https://efi.ed.ac.uk/research-awards-2/")
   list_urls.append("https://bbsrc.ukri.org/funding/filter/2019-bacterial-plant-diseases-coordination-team/")
   list_urls.append("https://www.airguide.soton.ac.uk/news/6594")
   list_urls.append("https://www.hfsp.org/funding/hfsp-funding/research-grants")
   list_urls.append("https://mrc.ukri.org/funding/browse/nrpnutrition/uk-nutrition-research-partnership-uk-nrp-travelling-skills-awards-for-nutrition-related-research/")
   list_urls.append("https://nerc.ukri.org/funding/application/currentopportunities/announcement-of-opportunity-enabling-research-in-smart-sustainable-plastic-packaging/")
   list_urls.append("https://www.ukri.org/funding/funding-opportunities/healthy-ageing-catalyst-awards-2020/")
   list_urls.append("https://wellcome.ac.uk/grant-funding/schemes/sir-henry-dale-fellowships")


   text_urls=[]
   for url in list_urls:
      text = extract_text_from_url(url)
      text_urls.append(text)
   
   custom_stop_words() 
   
   # The add_pipe function appends our functions to the default pipeline.
   nlp.add_pipe(norm_lemmatizer,name='lemmatizer',after='ner')
   nlp.add_pipe(remove_stopwords, name="stopwords", last=True)

   doc_list=[]
   for text in text_urls:
       pr = nlp(text)
       doc_list.append(pr)

   train_data = list(create_tagged_document(doc_list))
   #print(train_data[:1])

   # Init the Doc2Vec model
   #dm ({1,0}, optional) – Defines the training algorithm. 
   #If dm=1, ‘distributed memory’ (PV-DM) is used. Otherwise, distributed bag of words (PV-DBOW) is employed.
   
   model = gensim.models.doc2vec.Doc2Vec(vector_size=10, min_count=2, epochs=40)

   # Build the Volabulary
   model.build_vocab(train_data)

   # Train the Doc2Vec model
   model.train(train_data, total_examples=model.corpus_count, epochs=model.epochs)
  
   print(model.infer_vector(["Strategy", "Challenge", "Fund", "Working", "with", "business", "Skills", "Policy"]))
