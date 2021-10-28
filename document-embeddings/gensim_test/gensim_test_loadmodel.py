import gensim.downloader as api
import json

'''
Accessing pre-trained Wikipedia GloVe embeddings

https://kavita-ganesan.com/easily-access-pre-trained-word-embeddings-with-gensim/#.Xs5CQsbTWjQ

Also, read this one: https://rare-technologies.com/new-download-api-for-pretrained-nlp-models-and-datasets-in-gensim/


'''

# Get information about the model or dataset
info=api.info('glove-wiki-gigaword-50')
#print(json.dumps(info, indent=4))

print(info.keys())

# Download
model_glove = api.load("glove-wiki-gigaword-50")


# Similarities
print(model_glove.most_similar('blue'))
print(model_glove.wv.most_similar(positive=['dirty','grimy'],topn=10))
