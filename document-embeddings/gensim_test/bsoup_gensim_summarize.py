import requests
from bs4 import BeautifulSoup

import numpy as np
import re
from gensim.summarization import summarize, keywords
import gensim
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
      text = extract_text_from_url(url, clean_symb=False)
      text_urls.append(text)
   
   print(text_urls[0])
   for text in text_urls:
       pprint(summarize(text, word_count=20)) 
       print("------")
   
