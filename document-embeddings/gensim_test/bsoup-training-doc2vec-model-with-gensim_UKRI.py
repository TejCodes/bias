''' Following the example

Extending  bsoup-training-doc2vec-model-with-gensim.py.
It automatically extracts all the URLs from UKRI funding op. website (53 documents) and 
it builds a doc2vec with them. 

'''
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd 
import multiprocessing
import gc
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from gensim.utils import simple_preprocess


def extract_links_from_url(url_input):
    r = requests.get(url_input)
    text = BeautifulSoup(r.text, 'html.parser')
    url_list=[]

    remove_links = ['/funding/', '/funding/how-to-apply/', '/funding/funding-opportunities/', '/funding/information-for-award-holders/', '/funding/peer-review/', '/funding/funding-data/', '/skills/funding-for-research-training/', '/funding/how-to-apply/']

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


class MyCorpus():
    def __init__(self, train_data):
        self.train_data = train_data
        
    def __iter__(self):
        p = PorterStemmer()
        for i in range(len(self.train_data)):
            doc = self.train_data['text'][i]
            doc = re.sub(r'\S*@\S*\s?', '', doc, flags=re.MULTILINE) # remove email
            doc = re.sub(r'http\S+', '', doc, flags=re.MULTILINE) # remove web addresses
            doc = re.sub("\'", "", doc) # remove single quotes
            doc = remove_stopwords(doc)
            doc = p.stem_sentence(doc)
            words = simple_preprocess(doc, deacc=True)
            yield TaggedDocument(words=words, tags=[self.train_data['documentId'][i]])


class Doc2VecTrainer(object):
    def __init__(self, train_corpus):
        self.train_corpus = train_corpus

    def run(self, load_existing=None, model_path=None):
        print('app started')

        cores = multiprocessing.cpu_count()
        print('num of cores is %s' % cores)
        gc.collect()
        if load_existing:
            print('loading an exiting model')
            model = Doc2Vec.load(model_path)
        else:
            print('reading training corpus from %s' % self.train_corpus)
            corpus_data = MyCorpus(self.train_corpus)

            # Init the Doc2Vec model
            model_dimensions = 300
            #dm ({1,0}, optional) – Defines the training algorithm. 
	    #If dm=1, ‘distributed memory’ (PV-DM) is used. Otherwise, distributed bag of words (PV-DBOW) is employed.
            #vector_size (int, optional) – Dimensionality of the feature vectors.
            #window (int, optional) – The maximum distance between the current and predicted word within a sentence.
            #alpha (float, optional) – The initial learning rate.
            #min_alpha (float, optional) – Learning rate will linearly drop to min_alpha as training progresses.

            #seed (int, optional) -  Seed for the random number generator
            #min_count (int, optional) – Ignores all words with total frequency lower than this.
            #max_vocab_size (int, optional) – Limits the RAM during vocabulary building
            #sample (float, optional) – The threshold for configuring which higher-frequency words are randomly downsampled, useful range is (0, 1e-5).
            #epochs (int, optional) – Number of iterations (epochs) over the corpus
            #negative (int, optional) – Specifies how many “noise words” should be drawn (usually between 5-20) 

            model = Doc2Vec(vector_size=model_dimensions, window=10, min_count=2, sample=1e-4, negative=5, workers=cores, dm=1, epochs=40)

            # Build the Volabulary
            print('building vocabulary...')
            model.build_vocab(corpus_data)

            # Train Model
            model.train(corpus_data, total_examples=model.corpus_count, epochs=20)
            
            # Save Model using two formats
            model.save("doc2vec_model")
            model.save_word2vec_format("word2vec_model")

        print('total docs learned %s' % (len(model.docvecs)))


if __name__ == '__main__':
   
   list_urls=[]
   url="https://www.ukri.org/funding/funding-opportunities/"
   list_urls = extract_links_from_url(url)

   data = []
   id = 0
   for url in list_urls:
      text = extract_text_from_url(url)
      data.append([text, id])
      id += 1
   df = pd.DataFrame(data, columns = ['text', 'documentId']) 

   model = Doc2VecTrainer(df)
   model.run()

