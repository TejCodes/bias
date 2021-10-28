import requests
from bs4 import BeautifulSoup
from gensim.summarization import summarize, keywords
import numpy as np
import re

import gensim
from gensim.test.utils import common_texts
import gensim.corpora as corpora
from gensim.models import LdaModel, LdaMulticore

import spacy
from spacy.lemmatizer import Lemmatizer
from spacy.lang.en.stop_words import STOP_WORDS
import en_core_web_lg

from pprint import pprint

'''
The objective of topic models is to extract the underlying topics from a given collection of text documents. Each document in the text is considered as a combination of topics and each topic is considered as a combination of related words.

Topic modeling can be done by algorithms like Latent Dirichlet Allocation (LDA) and Latent Semantic Indexing (LSI).

In both cases you need to provide the number of topics as input. The topic model, in turn, will provide the topic keywords for each topic and the percentage contribution of topics in each document.
'''

nlp = spacy.load("en")

def interpret_LDA(lda_model, corpus):

    # The topic(s) that document belongs to along with percentage.
    # The topic(s) each word in that document belongs to.
    # The topic(s) each word in that document belongs to AND the phi values.
    # Phi value is the probability of the word belonging to that particular topic. 
    #And the sum of phi values for a given word adds up to the number of times that word occurred in that document.

    for c in lda_model[corpus[:]]:
        print("Document Topics      : ", c[0])      # [(Topics, Perc Contrib)]
        print("Word id, Topics      : ", c[1][:3])  # [(Word id, [Topics])]
        print("Phi Values (word id) : ", c[2][:3])  # [(Word id, [(Topic, Phi Value)])]
        print("Word, Topics         : ", [(dictionary[wd], topic) for wd, topic in c[1][:3]])   # [(Word, [Topics])]
        print("Phi Values (word)    : ", [(dictionary[wd], topic) for wd, topic in c[2][:3]])  # [(Word, [(Topic, Phi Value)])]
        print("------------------------------------------------------\n")

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

   #print(doc_list[0])
   # Creates, which is a mapping of word IDs to words.
   dictionary = corpora.Dictionary(doc_list)

   # Filter out words that occur less than 20 documents, or more than 50% of the documents.
   #dictionary.filter_extremes(no_below=2, no_above=0.5) 
   dictionary.filter_extremes(no_above=0.7) 

   # Turns each document into a bag of words.
   corpus = [dictionary.doc2bow(doc) for doc in doc_list]

   print('Number of unique tokens: {}'.format(len(dictionary)))
   print('Number of documents: {}'.format(len(corpus)))

   lda_model = LdaModel.load("lda_common_corpus.model")
   top_topics = lda_model.top_topics(corpus) #, num_words=20)
   pprint(top_topics)


