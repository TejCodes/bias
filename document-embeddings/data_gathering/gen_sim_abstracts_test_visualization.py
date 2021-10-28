import os   
import pandas as pd
from gensim.models.doc2vec import Doc2Vec
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt



if __name__ == "__main__":

      
    # Model wiht keywords
    model= Doc2Vec.load('keywords.doc2vec', mmap='r')
    
    # Model with abstract + title
    #model= Doc2Vec.load('doc2vec.model', mmap='r')
    
    vocab = list(model.wv.vocab)
    
    X = model[vocab]
    #tsne = TSNE(n_components=2)
    
    tsne = TSNE(n_components=2, verbose=1, random_state=0, angle=.99, init='pca')
    
    X_tsne = tsne.fit_transform(X)
    df = pd.DataFrame(X_tsne, index=vocab, columns=['x', 'y'])
    plt.figure(num=1, figsize=(80, 80), facecolor="w", edgecolor="k")

    plt.scatter(df['x'], df['y'], s=0.4, alpha=0.4)
    for word, pos in df.iterrows():
        plt.annotate(word, pos)

    plt.savefig("out_doc2vec_keywords.png", dpi=90)
    print("saved output to ./out_doc2vec.png\n")

