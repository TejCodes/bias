import json
import os

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


mapping = {
    "mappings": {
        "properties": {
        "title": {"type": "text"},
        "content": {"type": "text"},
        "visibility": {"type": "keyword"},
        "keywords": {"type": "text"},
        "source": {
            "type": "object",
            "enabled": False
        },
        "experts": {"type": "text"},
        "date": "date",
        }
    }
}

index_name = 'expertise'

def gen_documents(publications):
    for i, publication in enumerate(publications):
        body = {
            'title': publication['title'],
            'experts': publication['authors'],
            'content': publication['abstract'],
            'source': {
                'ref': 'Edinburgh Research Explorer',
            },
            'visibility': None, # public records
        }
        body['source'].update(publication['citation'])
        if 'date' in publication:
            body['date'] = publication['date']
        if 'keywords' in publication:
            body['keywords'] = publication['keywords']
        
        yield {
            "_index": index_name,
            "_source": body,
        }
    
    print(f'\nInserted {i} documents.')

if __name__ == "__main__":
    es = Elasticsearch()

    with open(os.path.join(os.path.dirname(__file__), 'epcc_publications.json')) as f:
        publications = json.load(f)

    es.indices.delete(index=index_name, ignore=[400, 404])
    es.indices.create(index=index_name, body=mapping, ignore=400)

    bulk(es, gen_documents(publications))

