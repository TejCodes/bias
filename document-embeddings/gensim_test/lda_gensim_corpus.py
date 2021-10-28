from gensim.test.utils import common_texts
from gensim.corpora.dictionary import Dictionary
from gensim.test.utils import datapath
from gensim.models import LdaModel, LdaMulticore
from pprint import pprint

# Create a corpus from a list of texts

dictionary = Dictionary(common_texts)
corpus = [dictionary.doc2bow(text) for text in common_texts]

#Train the model on the corpus.

lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=10)
lda_model.save('lda_common_corpus.model')
top_topics = lda_model.top_topics(corpus) #, num_words=20)
pprint(top_topics)
