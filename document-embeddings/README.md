# Documents Embeddings 


Three Python natural language processing (NLP) libraries are being explored:

- Spacy is a natural language processing (NLP) library for Python designed to have fast performance, and with word embedding models built in, it’s perfect for a quick and easy start.

- TextPipe is a Python package for converting raw text in to clean, readable text and extracting metadata from that text. Its functionalities include transforming raw text into readable text by removing HTML tags and extracting metadata such as the number of words and named entities from the text. 
	- Identify the language of text
  	- Extract the number of words, number of sentences, named entities from a text
  	- Calculate the complexity of a text
  	- Obtain text metadata by specifying a pipeline containing all desired elements
  	- Obtain sentiment (polarity and a subjectivity score)
  	- Generates word counts
	- Computes minhash for cheap similarity estimation of documents

- Gensim is a topic modelling library for Python that provides access to Word2Vec and other word embedding algorithms for training, and it also allows pre-trained word embeddings that you can download from the internet to be loaded.


# Reviewing Models

## Bag-of-words Model

This model transforms each document to a fixed-length vector of integers. For example, given the sentences:

    John likes to watch movies. Mary likes movies too.

    John also likes to watch football games. Mary hates football.

The model outputs the vectors:

    [1, 2, 1, 1, 2, 1, 1, 0, 0, 0, 0]

    [1, 1, 1, 1, 0, 1, 0, 1, 2, 1, 1]

Each vector has 10 elements, where each element counts the number of times a particular word occurred in the document. The order of elements is arbitrary. In the example above, the order of the elements corresponds to the words: ["John", "likes", "to", "watch", "movies", "Mary", "too", "also", "football", "games", "hates"].


Effective but bag-of-words model does not attempt to learn the meaning of the underlying words, and as a consequence, the distance between vectors doesn’t always reflect the difference in meaning. The Word2Vec model addresses this second problem.

## Word2Vec Model

Word2Vec is a more recent model that embeds words in a lower-dimensional vector space using a shallow neural network. The result is a set of word-vectors where vectors close together in vector space have similar meanings based on context, and word-vectors distant to each other have differing meanings. For example, strong and powerful would be close together and strong and Paris would be relatively far.

Gensim’s Word2Vec class implements this model.

With the Word2Vec model, we can calculate the vectors for each word in a document. But what if we want to calculate a vector for the entire document? For that, it is better to use Doc2Vec Model

## Doc2Vec Model

Doc2Vec usually outperforms such simple-averaging of Word2Vec vectors. The basic idea is: act as if a document has another floating word-like vector, which contributes to all training predictions, and is updated like other word-vectors, but we will call it a doc-vector. Gensim’s Doc2Vec class implements this algorithm.

There are two implementations:

- Paragraph Vector - Distributed Memory (PV-DM): The doc-vectors are obtained by training a neural network on the synthetic task of predicting a center word based an average of both context word-vectors and the full document’s doc-vector.

- Paragraph Vector - Distributed Bag of Words (PV-DBOW): The doc-vectors are obtained by training a neural network on the synthetic task of predicting a target word just from the full document’s doc-vector. (It is also common to combine this with skip-gram testing, using both the doc-vector and nearby word-vectors to predict a single target word, but only one at a time.)



# Python Environment

Create a new conda environment and install the required packages:

```
conda create --name oppmatch_model python=3.8 pandas lxml
conda activate oppmatch_model

pip install gensim
pip install spacy
pip install nltk
pip install beautifulsoup4
pip install elasticsearch
pip install neo4j
pip install mysqlclient
pip install feedparser
pip install dateparser
```

For spaCy download pretrained statistical models for English:
```
python -m spacy download en_core_web_lg
```
