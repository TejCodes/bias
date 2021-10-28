import base64
from io import BytesIO
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wordcloud import WordCloud, STOPWORDS

from .elastic_search import get_profile_documents, get_profile_document_ids, get_word_frequencies


def plot_profile_wordcloud(pure_id):
    doc_ids = [d.meta.id for d in get_profile_document_ids(pure_id)]
    all_words = get_word_frequencies(doc_ids)
    if not all_words:
        return None
    wordcloud = WordCloud(
        width = 600, height = 400,
        background_color ='white',
        min_font_size = 10).generate_from_frequencies(all_words) 

    plt.figure(figsize = (8, 8), facecolor = None) 
    plt.imshow(wordcloud) 
    plt.axis("off") 
    plt.tight_layout(pad = 0) 
    buf = BytesIO()
    plt.savefig(buf, format='png')
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()
    return image_base64

def get_documents_dict(pure_id):
    for doc in get_profile_documents(pure_id):
        yield({'document': doc})

def create_profile_graph(pure_id):
    result = create_vis_graph(get_documents_dict(pure_id), root_id=pure_id)
    return result

def create_vis_graph(similar_docs, root_id='ROOT'):
    nodes = {root_id: {'id': 'ROOT', 'label': '', 'group': 'root'}}
    edges = set()
    persons = {}
    for docsim in similar_docs:
        document = docsim['document']
        doc_id = document['document_id']
        if 'research_output' in document['type']:
            doctype = 'research_output'
        elif 'project' in document['type']:
            doctype = 'project'
        nodes[doc_id] = {
            'id': doc_id, 
            'group': doctype, 
            'label': f'{document["title"][:40]}...',
            'title': document['title'],
        }
        edges.add(('ROOT', doc_id))
        for person in document['source']['names']:
            person_id = person['uuid']
            nodes[person_id] = {
                'id': person_id, 
                'group': 'person', 
                'label': person['name'],
                'title': person['name'],
            }
            edges.add((doc_id, person_id))
    nodes[root_id]['group'] = 'root'
    return {'nodes': list(nodes.values()), 'edges': [{'from': e[0], 'to': e[1]} for e in edges]}

