import configparser
import os
from tqdm import tqdm
import json
from gensim.models.doc2vec import Doc2Vec
from elasticsearch import Elasticsearch

from doc2vec_prep import stem_text, clean_text, generate_documents_es
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

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    profile_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profiles.json')
    if not os.path.isfile(profile_data):
        profile_data = None

    with open('../common_files/constants.json') as f:
        constants = json.load(f)
    elastic_client = Elasticsearch([{'host': constants["ES_HOST_URL"], 'port': constants["ES_PORT"]}])
    train_documents = list(tqdm(generate_documents_es(elastic_client, clean_text, min_words=15, profile_data=profile_data)))
    print(f'Created {len(train_documents)} tagged documents.')
    model = Doc2Vec(**hyperparams)
    print('Build vocabulary')
    model.build_vocab(train_documents)
    for epoch in range(100):
        print(f'Train model: epoch={epoch}')
        model.train(train_documents, total_examples=model.corpus_count, epochs=1)
        model.alpha -= 0.0002
        model.min_alpha = model.alpha

    # Save the model
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'doc2vec_roag.model')
    model.save(model_path)
    print(f'Saved model to {model_path}')
