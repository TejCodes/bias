import argparse
import json
import os
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


mapping = {
    "mappings": {
        "properties": {
        "title": {"type": "text"},
        "content": {"type": "text"},
        "visibility": {"type": "keyword"},
        "keywords": {"type": "text"},
        "type": {"type": "keyword"},
        "document_id": {"type": "keyword"},
        "source": {
            "type": "object",
            "enabled": False
        },
        "experts": {"type": "keyword"},
        "startDate": {"type": "date"},
        "endDate": {"type": "date"},
        }
    }
}

index_name = 'expertise'

mapping_people = {
    "mappings": {
        "properties": {
            "uuid": {"type": "keyword"},
            "name": {"type": "text"},
            "url": {"type": "keyword", "enabled": False}
        }
    }
}

index_name_people = 'experts'

def get_date(date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f%z')
    except ValueError:
        # try another format
        d = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S%z')
    return d.date()

def gen_publications(publications):

    for pid, publication in publications.items():
        body = {
            'title': publication['title'],
            'experts': [a['uuid'] for a in publication['authors']],
            'content': publication['abstract'],
            'visibility': None, # public records,
            'type': ['ROAG', 'publication'],
            'document_id': pid,
            'source': {
                'url': publication['url'],
                'names': publication['authors']
            }
        }
        if 'date' in publication and publication['date']:
            body['startDate'] = str(get_date(publication['date']))
        if 'keywords' in publication:
            body['keywords'] = publication['keywords']
        
        yield {
            "_index": index_name,
            "_source": body,
        }
    
    print(f'Inserted {len(publications)} documents.')

def gen_projects(projects):

    for pid, project in projects.items():
        body = {
            'title': project['title'],
            'experts': [a['uuid'] for a in project['people']],
            'content': project['description'],
            'visibility': None, # public records,
            'type': ['ROAG', 'project'],
            'document_id': pid,
            'source': {
                'names': project['people']
            }
        }
        if 'startDate' in project and project['startDate']:
            body['startDate'] = str(get_date(project['startDate']))
        if 'endDate' in project and project['endDate']:
            body['endDate'] = str(get_date(project['endDate']))
        if 'keywords' in project:
            body['keywords'] = project['keywords']
        
        yield {
            "_index": index_name,
            "_source": body,
        }
    
    print(f'Inserted {len(projects)} documents.')

def gen_people(people):
    for person_id, person in people.items():
        yield {
            "_index": index_name_people,
            "_source": person
        }
    print(f'Inserted {len(people)} documents into experts index.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pub', '--research-outputs', help='Research outputs', required=True)
    parser.add_argument('-proj', '--projects', help='Projects', required=True)
    parser.add_argument('-e', '--experts', help='Experts', required=True)
    args = parser.parse_args()

    es = Elasticsearch()

    es.indices.delete(index=index_name, ignore=[400, 404])
    es.indices.create(index=index_name, body=mapping, ignore=400)

    es.indices.delete(index=index_name_people, ignore=[400, 404])
    es.indices.create(index=index_name_people, body=mapping_people, ignore=400)

    with open(os.path.join(os.path.dirname(__file__), args.research_outputs)) as f:
        publications = json.load(f)
        bulk(es, gen_publications(publications))
    with open(os.path.join(os.path.dirname(__file__), args.projects)) as f:
        projects = json.load(f)
        bulk(es, gen_projects(projects))
    with open(os.path.join(os.path.dirname(__file__), args.experts)) as f:
        people = json.load(f)
        bulk(es, gen_people(people))

