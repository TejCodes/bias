import re

from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from gensim.models.doc2vec import TaggedDocument 

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


def generate_research_output(driver, clean_func=stem_text, min_words=10):
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

def generate_gtr_projects(driver, clean_func=stem_text, min_words=10):
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

def generate_documents(driver, clean_func=clean_text, min_words=10):
    print(f'Preprocessing function: {clean_func.__name__}')
    print(f'Minimum document length: {min_words} words')
    yield from generate_research_output(driver, clean_func)
    yield from generate_gtr_projects(driver, clean_func, min_words)
