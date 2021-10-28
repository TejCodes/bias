from collections import defaultdict
import uuid

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MoreLikeThis

from django.urls import reverse

from .doc2vec import nlp
from .models import UserProfile

es = Elasticsearch()

def generate_publications(name):
    s = Search().using(es).index('expertise').query("match", experts=name)
    response = s.execute()
    for hit in s.scan():
        yield hit

def get_profile_search(pure_id):
    return Search().using(es).index('expertise').query("match", experts=pure_id)

def get_profile_document_ids(pure_id):
    s = get_profile_search(pure_id).index('expertise').source(['document_id'])
    response = s.execute()
    yield from s.scan()
    
def get_profile_documents(pure_id, source=None):
    s = get_profile_search(pure_id).index('expertise').source(source)
    response = s.execute()
    yield from s.scan()


def get_word_frequencies(doc_ids):
    fields = ['abstract', 'tech_abstract', 'impact']
    result = defaultdict(int)
    for doc_id in doc_ids:
        response = es.termvectors(
            id=doc_id,
            index='expertise',
            fields=fields,
            positions=False,
            offsets=False)
        # profile document query sometimes returns documents that can't be found
        if not response['found']:
            continue
        term_vectors = response['term_vectors']
        for field in fields:
            if field in term_vectors:
                for term, val in term_vectors['abstract']['terms'].items():
                    if not nlp.vocab[term].is_stop:
                        result[term] += val['term_freq']
    return result

def get_document(doc_id):
    s = Search().using(es).index('expertise').query("match", document_id=doc_id)
    response = s.execute()
    if response.hits.total.value > 0:
        return response.to_dict()['hits']['hits'][0]['_source']
    return None

def get_person(person_id):
    response = es.search(index='experts',
        body = {
            "query": {
                "match" : { "uuid": person_id }
            }
        }
    )
    if response['hits']['hits']:
        return response['hits']['hits'][0]['_source']
    else:
        return None

def more_like_this(text, topn=10000):
    s = Search().using(es).query(MoreLikeThis(
        like=text,
        fields=['abstract', 'tech_abstract', 'impact'],
        min_term_freq=1,
        max_query_terms=12))
    response = s.execute()
    results = defaultdict(int)
    for d in s[:topn]:
        results[d.document_id] = max(results[d.document_id], d.meta.score)
    return [(k, v) for k,v in results.items()]


def generate_user_profiles(index_name):
    users = {}
    for profile in UserProfile.objects.all():
        user_settings = profile.user.settings_set.first()
        if user_settings and user_settings.uuid:
            user_id = user_settings.uuid
            person = get_person(user_id)
        # else:
        #     user_id = profile.user.id
        users[profile.user.id] = {
            'name': person['name'],
            'url': person['url'],
            'uuid': person['uuid'],
        }
    total_generated = 0
    for profile in UserProfile.objects.all():
        body = {
            'title': profile.name,
            'abstract': profile.text,
            'experts': [users[profile.user.id]['uuid']],
            'type': ['OM', 'profile'],
            'visibility': None, # public records,
            'document_id': f'om-{profile.id}', # this doesn't overlap with the ROAG ids
            'source': {
                'names': [users[profile.user.id]],
                'url': reverse('person', kwargs={'person_id': profile.user.id}),
                'date': profile.created.isoformat(),
            }
        }
        total_generated += 1
        yield {
            "_index": index_name,
            "_source": body,
        }

    print(f'Generated {total_generated} profiles')

def insert_profiles():
    bulk(es, generate_user_profiles())