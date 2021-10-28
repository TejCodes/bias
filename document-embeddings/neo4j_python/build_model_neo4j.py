import configparser
import os
from tqdm import tqdm

from neo4j import GraphDatabase

import gensim
from gensim.models.doc2vec import Doc2Vec, TaggedDocument 

from doc2vec_prep import stem_text

# Init the Doc2Vec model
hyperparams  = {
    'vector_size': 300,
    'min_count': 2,
    'epochs': 100,
    'window': 15,
    'negative': 5, 
    'sampling_threshold': 1e-5, 
    'workers': 8, 
    'dm': 0
}

min_length = 10

def generate_research_output(driver):
    query = '''
        MATCH (r:PURE:ResearchOutput) 
        RETURN distinct(r)
    '''
    gen_docs = 0
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            resout_node = r['r']
            resout_id = resout_node['uuid']
            if resout_node['abstract_value'] != '':
                text = resout_node['abstract_value'] + resout_node['title']
                words = stem_text(text)
                if len(words) >= min_length:
                    gen_docs += 1
                    yield TaggedDocument(words=words, tags=[resout_id])
    print(f'Generated {gen_docs} research outputs')

def generate_gtr_projects(driver):
    # find all projects in the University of Edinburgh
    query = '''
        MATCH (proj:GTR:Project)
        -- (:GTR:Organisation {name: 'University of Edinburgh'}) 
        RETURN distinct(proj)
    '''
    gen_docs = 0
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            project = r['proj']
            words = stem_text(
                project['title'] 
                + project['techAbstractText']
                + project['abstractText']
                + project['potentialImpact']
            )
            if len(words) >= min_length:
                gen_docs += 1
                yield TaggedDocument(words=words, tags=[project['id']])
    print(f'Generated {gen_docs} project documents')

def generate_documents(driver):
    yield from generate_research_output(driver)
    yield from generate_gtr_projects(driver)


if __name__ == "__main__":

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    uri = "bolt://roag.is.ed.ac.uk:7687"
    driver = GraphDatabase.driver(uri, auth=(config['auth']['USERNAME'], config['auth']['PASSWORD']))

    model = Doc2Vec(**hyperparams)
    print('Build vocabulary')
    model.build_vocab(tqdm(generate_documents(driver)))
    print('Train model')
    model.train(
        tqdm(generate_documents(driver)),
        total_examples=model.corpus_count,
        epochs=model.epochs)

    # Save the model
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'doc2vec_neo4j_v1.model')
    model.save(model_path)
    print(f'Saved model to {model_path}')
