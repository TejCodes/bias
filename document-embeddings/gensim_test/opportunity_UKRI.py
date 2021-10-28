''' Following the example

Extending  bsoup-training-doc2vec-model-with-gensim.py.
It automatically extracts all the URLs from UKRI funding op. website (53 documents) and 
it builds a doc2vec with them. 

'''

import spacy
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd 
import gc
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess

from collections import Counter
from string import punctuation


def get_keywords_dates(text):
    result = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN']
    doc = nlp(text.lower())
    dates=[]
    for entity in doc.ents:
        if entity.label_ == 'DATE':
            dates.append(entity.text)
        #print(entity.text, entity.label_)
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        
        if(token.pos_ in pos_tag):
            result.append(token.text)
                
    return result,dates


def stem_text(text):
    p = PorterStemmer()
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE) # remove email
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE) # remove web addresses
    text = re.sub("\'", "", text) # remove single quotes
    text = remove_stopwords(text)
    text = p.stem_sentence(text)
    return simple_preprocess(text, deacc=True)


def extract_links_from_url(url_input):
    r = requests.get(url_input)
    text = BeautifulSoup(r.text, 'html.parser')
    url_list=[]

    remove_links = ['/funding/', '/funding/how-to-apply/', '/funding/funding-opportunities/', '/funding/information-for-award-holders/', '/funding/peer-review/', '/funding/funding-data/', '/skills/funding-for-research-training/', '/funding/how-to-apply/', '/funding/the-new-ukri-funding-service/']

    for link in text.findAll('a'):
        link_data = link.get('href')
        if "funding" in link_data:
            if link_data not in remove_links:
                if "http" not in link_data:
                     link_data= "https://www.ukri.org"+link_data
                url_list.append(link_data)

    return url_list


def extract_text_from_url(url_input):
    r = requests.get(url_input)
    text = BeautifulSoup(r.text, 'html.parser').get_text()
    return text


if __name__ == '__main__':

   nlp = spacy.load("en_core_web_lg")   
   list_urls=[]
   url="https://www.ukri.org/funding/funding-opportunities/"
   list_urls = extract_links_from_url(url)

   data = []
   id = 0
   for url in list_urls[:1]:
      text = extract_text_from_url(url)
      s_text= stem_text(text)
      keywords, dates = get_keywords_dates(text)
      hashtags = [('#' + x) for x in set(keywords)]
      join_hashtags=' '.join(hashtags)
      print("URL:{} - Matches {}".format(url, dates))
      data.append([s_text, id, join_hashtags, dates])
      id += 1

   df = pd.DataFrame(data, columns = ['text', 'documentId', 'hashtags', 'dates']) 
   print(df['dates'])

