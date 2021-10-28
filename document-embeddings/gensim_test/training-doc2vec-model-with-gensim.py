''' Following the example

http://yaronvazana.com/2018/01/20/training-doc2vec-model-with-gensim/
Improved - some errors in the original code

'''
import re
import pandas as pd 
import multiprocessing
import gc
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 
from gensim.utils import simple_preprocess

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
            model_dimensions = 10
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

   data = [['this is a document 1', 0], ['this is the document 2', 1] , ['I want to go to the beach', 2]]
   df = pd.DataFrame(data, columns = ['text', 'documentId']) 
   model = Doc2VecTrainer(df)
   model.run()

