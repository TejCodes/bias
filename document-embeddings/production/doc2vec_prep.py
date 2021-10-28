import json
import re

from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from gensim.models.doc2vec import TaggedDocument 

from elasticsearch import Elasticsearch
import json, requests

index_expertise="expertise"

search_PURE = {
    "_source": {
            "includes": [ "document_id", "title", "abstract" ]
        },
    "query": {
        "match": {
            "type": "PURE" 
        }
    }
}

search_GTR = {
    "_source": {
            "includes": [ "document_id", "title", "abstract", "tech_abstract", "impact" ]
        },
    "query": {
        "match": {
            "type": "GTR" 
        }
    }
}

def stem_text(text):
    p = PorterStemmer()
    text = re.sub(r'\S*@\S*\s?', '', text, flags=re.MULTILINE) # remove email
    text = re.sub(r'http\S+', '', text, flags=re.MULTILINE) # remove web addresses
    text = re.sub("\'", "", text) # remove single quotes
    text = remove_stopwords(text)
    text = p.stem_sentence(text)
    return simple_preprocess(text, deacc=True)

import spacy
nlp = spacy.load('en_core_web_lg')

def clean_text(corpus):
    # --- remove if not alphanumeric:
    corpus = re.sub('[\W_]+', ' ', corpus)
    # --- replace numbers with #
    corpus = re.sub(r'\b\d+\b', '#', corpus)
    # --- remove new line character
    corpus = re.sub('\n', ' ', corpus)
    # --- remove words containing numbers
    corpus = re.sub('\w*\d\w*', '', corpus)
    # --- remove one-letter words in square brackets
    corpus = re.sub(r"\b[a-zA-Z]\b", '', corpus)
    # --- remove words with one characters
    corpus = re.sub(r"\b\w{1}\b", '', corpus)
    # --- remove multiple spaces in string
    corpus = re.sub(' +', ' ', corpus)
    # --- make lowercase
    corpus = corpus.lower()
    corpus = nlp(corpus)
    
    all_texts = []
    for sentence in list(corpus.sents):
        # --- lemmatization, remove punctuation
        txt = [token.lemma_ for token in sentence if not token.is_punct and not token.is_stop]
        all_texts.append(txt)
    return [val for sublist in all_texts for val in sublist]


def generate_research_output(driver, clean_func=clean_text, min_words=10):
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
                if len(words) >= min_words:
                    gen_docs += 1
                    yield TaggedDocument(words=words, tags=[resout_id])
    print(f'Generated {gen_docs} research outputs')

no_abstract = 'Abstracts are not currently available in GtR for all funded research.'

def generate_gtr_projects(driver, clean_func=clean_text, min_words=10):
    # find all projects in the University of Edinburgh
    query = '''
        MATCH (proj:GTR:Project)
        -- (:GTR:Organisation {name: 'University of Edinburgh'}) 
        RETURN distinct(proj)
    '''
    gen_docs = 0
    all_docs = 0
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            all_docs += 1
            project = r['proj']
            proj_text = f"""
                {project['title']}
                {project['techAbstractText']}
                {project['abstractText']}
                {project['potentialImpact']}
            """
            if no_abstract in proj_text:
                # keep only the title if abstract is default filler by GtR
                proj_text = project['title']
            words = clean_func(proj_text)
            if len(words) >= min_words:
                gen_docs += 1
                yield TaggedDocument(words=words, tags=[project['id']])
    print(f'Generated {gen_docs} project documents from {all_docs} total.')


def generate_profiles(input_file, clean_func=clean_text):
    with open(input_file) as f:
        profiles = json.load(f)
    for p in profiles:
        words = clean_func(p['text'])
        yield TaggedDocument(words=words, tags=[p['document_id']])
    print(f'Generated {len(profiles)} profiles.')

def generate_documents(driver, clean_func=clean_text, min_words=10, profile_data=None):
    print(f'Preprocessing function: {clean_func.__name__}')
    print(f'Minimum document length: {min_words} words')
    yield from generate_research_output(driver, clean_func)
    yield from generate_gtr_projects(driver, clean_func, min_words)
    if profile_data:
        yield from generate_profiles(profile_data, clean_func)

def generate_documents_es(elastic_client, clean_func=clean_text, min_words=10, profile_data=None):
    print(f'Preprocessing function: {clean_func.__name__}')
    print(f'Minimum document length: {min_words} words')
    #elastic_client = Elasticsearch()
    yield from generate_research_output_es(elastic_client, clean_func)
    yield from generate_gtr_projects_es(elastic_client, clean_func, min_words)
    if profile_data:
        yield from generate_profiles(profile_data, clean_func)

def generate_research_output_es(elastic_client, clean_func=clean_text, min_words=10):
    gen_docs = 0
    resp = elastic_client.search(index=index_expertise, body=search_PURE, size=1000, scroll = '10000s')
    old_scroll_id = resp['_scroll_id']
    while len(resp['hits']['hits']):
        resp = elastic_client.scroll(
             scroll_id = old_scroll_id,
             scroll = '10000s' # length of time to keep search context
        )
        # keep track of pass scroll _id
        old_scroll_id = resp['_scroll_id']
        for i in resp["hits"]["hits"]:
            resout_node=i['_source']
            resout_id = resout_node["document_id"]
            if resout_node['abstract'] != '':
                text = resout_node['abstract'] + resout_node['title']
                words = stem_text(text)
                if len(words) >= min_words:
                    gen_docs += 1
                    yield TaggedDocument(words=words, tags=[resout_id])

    print(f'Generated {gen_docs} research outputs')
no_abstract = 'Abstracts are not currently available in GtR for all funded research.'

def generate_gtr_projects_es(elastic_client, clean_func=clean_text, min_words=10):
    gen_docs = 0
    all_docs = 0
    # find all projects in the University of Edinburgh
    resp = elastic_client.search(index=index_expertise, body=search_GTR, size=1000, scroll = '10000s')
    no_abstract = 'Abstracts are not currently available in GtR for all funded research.'
    old_scroll_id = resp['_scroll_id']
    while len(resp['hits']['hits']):
        resp = elastic_client.scroll(
             scroll_id = old_scroll_id,
             scroll = '10000s' # length of time to keep search context
        )
        # keep track of pass scroll _id
        old_scroll_id = resp['_scroll_id']
        for i in resp["hits"]["hits"]:
            project=i['_source']
            proj_text = f"""
                  {project['title']}
                  {project['tech_abstract']}
                  {project['abstract']}
                  {project['impact']}
            """
            if no_abstract in proj_text:
                # keep only the title if abstract is default filler by GtR
                proj_text = project['title']
            words = clean_func(proj_text)
            all_docs += 1
            if len(words) >= min_words:
                gen_docs += 1
                yield TaggedDocument(words=words, tags=[project['document_id']])
    print(f'Generated {gen_docs} project documents from {all_docs} total.')

