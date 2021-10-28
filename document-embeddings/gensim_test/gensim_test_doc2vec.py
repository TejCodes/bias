''' Following
https://radimrehurek.com/gensim/auto_examples/tutorials/run_doc2vec_lee.html '''

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

import os
import gensim
import smart_open
import collections
import random

def read_corpus(fname, tokens_only=False):
    ''' 

    open the train/test file (with latin encoding)

    read the file line-by-line

    pre-process each line (tokenize text into individual words, remove punctuation, set to lowercase, etc)
    '''

    with smart_open.open(fname, encoding="iso-8859-1") as f:
        for i, line in enumerate(f):
            tokens = gensim.utils.simple_preprocess(line)
            if tokens_only:
                yield tokens
            else:
                # For training data, add tags
                yield gensim.models.doc2vec.TaggedDocument(tokens, [i])

# Set file names for train and test data
test_data_dir = os.path.join(gensim.__path__[0], 'test', 'test_data')

# Training our model using the Lee Background Corpus included in gensim, which contains 314 documents.
lee_train_file = os.path.join(test_data_dir, 'lee_background.cor')

# Testing our model using the shorter Lee Corpus which contains 50 documents.
lee_test_file = os.path.join(test_data_dir, 'lee.cor')

train_corpus = list(read_corpus(lee_train_file))
test_corpus = list(read_corpus(lee_test_file, tokens_only=True))

#print(train_corpus[:2])
#print("----")
#print(test_corpus[:2])


#We instantiate a Doc2Vec model with a vector size with 50 dimensions 
#and iterating over the training corpus 40 times. 
#We set the minimum word count to 2 in order to discard words with very few occurrences.

model = gensim.models.doc2vec.Doc2Vec(vector_size=50, min_count=2, epochs=40)

#Build a vocabulary, which is a dictionary (accessible via model.wv.vocab) of all of 
#the unique words extracted from the training corpus along with the count 
#(e.g., model.wv.vocab['penalty'].count for counts for the word penalty).

model.build_vocab(train_corpus)


# Train the model on the corpus. If the BLAS library is being used, this should take no more than 3 seconds. 
#If the BLAS library is not being used, this should take no more than 2 minutes, so use BLAS if you value your time.

model.train(train_corpus, total_examples=model.corpus_count, epochs=model.epochs)

#Use the trained model to infer a vector for any piece of text 
#by passing a list of words to the model.infer_vector function. 
#This vector can then be compared with other vectors via cosine similarity.

#vector = model.infer_vector(['only', 'you', 'can', 'prevent', 'forest', 'fires'])
#print(vector)

# To asses our new model we infer new vectors for each document of the training corpus, 
# compare the inferred vectors with the training corpus,
# and then returning the rank of the document based on self-similarity.
# We’re pretending as if the training corpus is some new unseen data and 
# then seeing how they compare with the trained mode.

ranks = []
second_ranks = []
for doc_id in range(len(train_corpus)):
    inferred_vector = model.infer_vector(train_corpus[doc_id].words)
    sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
    rank = [docid for docid, sim in sims].index(doc_id)
    ranks.append(rank)

    second_ranks.append(sims[1])


#Basically, greater than 95% of the inferred documents 
#are found to be most similar to itself and about 5% of the time 
# it is mistakenly most similar to another document. 
#Checking the inferred-vector against a training-vector is a sort of ‘sanity check’.

counter = collections.Counter(ranks)
print(counter)

#Example of checking the document similarity:
#print('Document ({}): «{}»\n'.format(doc_id, ' '.join(train_corpus[doc_id].words)))
#print(u'SIMILAR/DISSIMILAR DOCS PER MODEL %s:\n' % model)
#for label, index in [('MOST', 0), ('SECOND-MOST', 1), ('MEDIAN', len(sims)//2), ('LEAST', len(sims) - 1)]:
#    print(u'%s %s: «%s»\n' % (label, sims[index], ' '.join(train_corpus[sims[index][0]].words)))

# Testing the Model
# Pick a random document from the test corpus and infer a vector from the model
doc_id = random.randint(0, len(test_corpus) - 1)
inferred_vector = model.infer_vector(test_corpus[doc_id])
sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))

# Compare and print the most/median/least similar documents from the train corpus
print('Test Document ({}): «{}»\n'.format(doc_id, ' '.join(test_corpus[doc_id])))
print(u'SIMILAR/DISSIMILAR DOCS PER MODEL %s:\n' % model)
for label, index in [('MOST', 0), ('MEDIAN', len(sims)//2), ('LEAST', len(sims) - 1)]:
    print(u'%s %s: «%s»\n' % (label, sims[index], ' '.join(train_corpus[sims[index][0]].words)))
