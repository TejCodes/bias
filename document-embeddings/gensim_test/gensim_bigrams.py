import gensim.downloader as api
import gensim.corpora as corpora
import gensim.models

''' In paragraphs, certain words always tend to occur in pairs (bigram) or in groups of threes (trigram). Because the two words combined together form the actual entity. For example: The word ‘French’ refers the language or region and the word ‘revolution’ can refer to the planetary revolution. But combining them, ‘French Revolution’, refers to something completely different. 

The created Phrases model allows indexing, so, just pass the original text (list) to the built Phrases model to form the bigrams. An example is shown below:

'''


dataset = api.load("text8")
dataset = [wd for wd in dataset]

dct = corpora.Dictionary(dataset)
corpus = [dct.doc2bow(line) for line in dataset]

# Build the bigram models
bigram = gensim.models.phrases.Phrases(dataset, min_count=3, threshold=10)

# Construct bigram
print(bigram[dataset[0]])


# Build the trigram models
trigram = gensim.models.phrases.Phrases(bigram[dataset], threshold=10)

# Construct trigram
print(trigram[bigram[dataset[0]]])
