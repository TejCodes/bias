''' Following the example

Extending  bsoup-training-doc2vec-model-with-gensim_Academic.py.
It automatically extracts all the URLs from the School of Informatics (Academic Staff)
it builds a doc2vec with them. 


Using dblp API wrapper !!!!
https://github.com/mrksbrg/dblp-python

'''
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd 
import multiprocessing
import gc
import dblp
import re
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from gensim.utils import simple_preprocess


def extract_links_from_url(url_input, type=None):
    url_list=[]
    try:
        r = requests.get(url_input)
        text = BeautifulSoup(r.text, 'html.parser')
        print(text)
        for link in text.findAll('a'):
            link_data = link.get('href')
            try:
                if "staff/" in link_data:
                     if type == "epcc":
                        link_data="https://www.epcc.ed.ac.uk" + link_data
                     url_list.append([link_data, type])
            except:
                pass
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(SystemExit(e))
    return url_list


def extract_text_from_url(url_input):
    r = requests.get(url_input)
    text = BeautifulSoup(r.text, 'html.parser').get_text()
    return text

def extract_dbl_publications(url_input, type):
    r=Researcher(url_input, type)
    print("Researcher {} has {} publications in DBLP!".format(r.full_name, r.num_publications))
    return ''.join(map(str, r.list_publications))


class Researcher:
   def __init__(self,url,school):
       self.url = url
       print(self.url)
       self.school = school
       if self.school == "inf":
           print(self.url.split("/")[-1].split(".html")[0].replace("_", " "))
       elif self.school == "epcc":
           print(self.url.split("/")[-1].replace("dr-", "").replace("ms-", "").replace("mr-","").replace("-"," "))

   @property
   def full_name(self):
       if self.school == "inf":
           return self.url.split("/")[-1].split(".html")[0].replace("_", " ")
       elif self.school == "epcc":
           return self.url.split("/")[-1].replace("dr-", "").replace("ms-", "").replace("mr-","").replace("-"," ")

   @property
   def author(self):
       if dblp.search(self.full_name):
          return dblp.search(self.full_name)[0]
       else:
           return None
   @property
   def num_publications(self):
       if self.author:
          return len(self.author.publications)
       else:
          return 0

   @property
   def list_publications(self):
       list_pub=[]
       if self.author:
           for pub in self.author.publications:
              list_pub.append([pub.title, pub.journal, pub.year, pub.ee])
              print(list_pub[-1])
       return list_pub

   @property
   def research_profile(self):
       return [[self.author.name] + self.list_publications]
       

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
   
   list_staff=[]
   list_staff.append(["https://www.ed.ac.uk/informatics/people/academic","inf"])
   list_staff.append(["https://www.epcc.ed.ac.uk/about/staff","epcc"])
   list_staff_urls=[]
   for staff in list_staff:
       list_staff_urls.append(extract_links_from_url(staff[0],staff[1]))
   
   data = []
   id = 0
   for list_urls in list_staff_urls:
      if len(list_urls) > 0:
          for url, type in list_urls:
              print("URL Staff is {}".format(url))
              academic_text = extract_text_from_url(url)
              dblp_text = extract_dbl_publications(url, type)
              text = [academic_text] + dblp_text
              data.append([text, id])
              id += 1
   

   if len(data)> 0:
      df = pd.DataFrame(data, columns = ['text', 'documentId']) 
      model = Doc2VecTrainer(df)
      model.run()

