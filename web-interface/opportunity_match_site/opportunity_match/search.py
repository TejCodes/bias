from collections import defaultdict
import json
import os
import types
import requests

from .doc2vec import load_model, most_similar, clean_text
from .elastic_search import get_document, get_person, more_like_this
from . import models


class Search():
    
    def __init__(self, model, render_method):
        self.model=model
        self.render=types.MethodType(render_method, self)

def get_url(api_ref):
    try:
        response = requests.get(api_ref, headers={'Accept': 'application/json'})
        info = response.json()
        if info['identifiers']['identifier']:
            identifier =info['identifiers']['identifier'][0]['value']
            return f'https://gtr.ukri.org/projects?ref={identifier}'
    except:
        pass
    return None

def create_vis_graph(similar_docs):
    nodes = {'ROOT': {'id': 'ROOT', 'label': '', 'group': 'root'}}
    edges = []
    for docsim in similar_docs:
        document = docsim['document']
        doc_id = document['document_id']
        if 'research_output' in document['type']:
            doctype = 'research_output'
        elif 'project' in document['type']:
            doctype = 'project'
        elif 'profile' in document['type']:
            doctype = 'profile'
        else:
            doctype = 'other'
        nodes[doc_id] = {
            'id': doc_id, 
            'group': doctype, 
            'label': f'{document["title"][:40]}...',
            'title': document['title'],
        }
        edges.append({'from': 'ROOT', 'to': doc_id, })
        for person in document['source']['names']:
            person_id = person['uuid']
            nodes[person_id] = {
                'id': person_id, 
                'group': 'person', 
                'label': person['name'],
                'title': person['name'],
            }
            edges.append({'from': doc_id, 'to': person_id})
    return list(nodes.values()), edges

def create_ordering(similar_docs):
    person_score = defaultdict(lambda: 0)
    people = defaultdict(lambda: {'documents': []})
    for docsim in similar_docs:
        document = docsim['document']
        similarity = docsim['similarity']
        for person in document['source']['names']:
            person_id = person['uuid']
            people[person_id].update(person)
            people[person_id]['documents'].append(document)
            person_score[person_id] = person_score[person_id] + similarity
    total_score = sum(person_score.values())
    return sorted(
        [{
            'similarity': score/total_score, 
            'person': people[pid]
            } for pid, score in person_score.items()],
        key=lambda t: t['similarity'],
        reverse=True
    )

def create_results(similar_docs, resolve_urls=True):
    results = []
    for doc_id, similarity in similar_docs:
        document = get_document(doc_id)
        if document is None:
            # a document could be None if there are no UoE people
            continue
        if resolve_urls and 'project' in document['type']:
            proj_url = get_url(document['source']['url'])
            if proj_url:
                document['source']['href'] = document['source']['url']
                document['source']['url'] = proj_url
        results.append({'similarity': similarity, 'document': document})
    return results

def render_results(search, similar_docs):
    results = create_results(similar_docs, resolve_urls=True)
    nodes, edges = create_vis_graph(results)
    ordered_people = create_ordering(results)
    return (
        'opportunity_match/search_result_v1.html', 
        {
            'results': results,
            'experts': ordered_people,
            'search': search,
            'graph': {'nodes': nodes, 'edges': edges},
        })

def get_similar_docs_gensim(model, search):
    cleaned_text = clean_text(search.text)
    if len(cleaned_text) > 30:
        similar_docs = most_similar(model, search.text, topn=100)
    else:
        similar_docs = []
    return similar_docs

def get_more_like_this_es(keywords):
    if keywords:
        keywords_similar = more_like_this(keywords, topn=100)
    else:
        keywords_similar = []
    return keywords_similar

import pandas as pd
def normalise_and_sort(result_list):
    ad = None
    for results in result_list:
        if results:
            d = pd.DataFrame(results)
            d[1] = (d[1]-d[1].min())/(d[1].max()-d[1].min())
            if ad is None:
                ad = d
            else:
                ad = ad.append(d)
    if ad is None:
        return []
    ad.sort_values(1, inplace=True, ascending=False)
    return list(ad.itertuples(index=False, name=None))

def search_v1(self, search):
    cleaned_text = clean_text(search.text)
    keywords = search.keywords
    if len(cleaned_text) > 30:
        gensim_similar = get_similar_docs_gensim(self.model, search)
    else:
        gensim_similar = []
        keywords += ' ' + search.text
    keyword_similar = get_more_like_this_es(keywords)
    search_result = models.SearchResult(
        search=search,
        timestamp=search.timestamp,
        results=json.dumps({'embeddings': gensim_similar, 'keywords': keyword_similar}),
    ).save()
    return search_result

def create_search_graph(similar_searches, min_similarity=0.8):
    nodes = {'ROOT': {'id': 'ROOT', 'label': '', 'group': 'root'}}
    edges = []
    for simsearch in similar_searches:
        if simsearch['similarity'] >= min_similarity:
            search = simsearch['search']
            nodes[search.id] = {
                'id': search.id,
                'group': 'search',
                'label': f'{search.name}',
                'similarity': simsearch['similarity'],
            }
            edges.append({'from': 'ROOT', 'to': search.id, })
            person = simsearch['owner']
            person_node_id = f"p{person['id']}"
            nodes[person_node_id] = {
                'id': person_node_id,
                'person_id': person['id'],
                'group': 'person',
                'label': person['name'],
            }
            edges.append({'from': search.id, 'to': person_node_id})
    return list(nodes.values()), edges

def similar_searches(self, search):
    gensim_similar = get_similar_docs_gensim(self.model, search)
    results = []
    for search_id, similarity in gensim_similar:
        try:
            sim_search = models.Search.objects.get(id=search_id)
        except models.Search.DoesNotExist:
            continue
        try:
            settings = models.Settings.objects.get(user=sim_search.user)
            user_pureid = settings.uuid
        except models.Settings.DoesNotExist:
            user_pureid = ''
        results.append({
            'search': sim_search,
            'owner': {
                'name': f'{sim_search.user.first_name} {sim_search.user.last_name}',
                'uuid': user_pureid,
                'id': sim_search.user.id,
            },
            'similarity': similarity,
        })
    nodes, edges = create_search_graph(results)
    if len(nodes) == 1:
        return {}
    return {
        'searches': results,
        'graph': {'nodes': nodes, 'edges': edges},
    }

SEARCHES = {
    'v1': Search(model=load_model('doc2vec_roag.model'), render_method=search_v1),
    'search': Search(model=load_model('doc2vec_search.model'), render_method=similar_searches),
}    