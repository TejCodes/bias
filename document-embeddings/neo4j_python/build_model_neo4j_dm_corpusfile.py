import os

from gensim.models.doc2vec import Doc2Vec

# Init the Doc2Vec model
hyperparams  = {
    'dm': 1,
    'vector_size': 300,
    'window': 5,
    'alpha': 0.025,
    'min_alpha': 0.00025,
    'min_count': 2,
    'workers': 8
}
if __name__ == "__main__":

    corpus_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_text_preprocessed.txt')
    model = Doc2Vec(**hyperparams)
    print('Build vocabulary')
    model.build_vocab(corpus_file=corpus_file)
    for epoch in range(100):
        print(f'Train model: epoch={epoch}')
        model.train(
            corpus_file=corpus_file,
            total_examples=model.corpus_count,
            total_words=model.corpus_total_words,
            epochs=1)
        model.alpha -= 0.0002
        model.min_alpha = model.alpha

    # Save the model
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'doc2vec_neo4j_dm.model')
    model.save(model_path)
    print(f'Saved model to {model_path}')
