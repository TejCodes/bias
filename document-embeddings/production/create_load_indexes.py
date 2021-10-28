import json
import configparser
import os

from tqdm import tqdm

from neo4j import GraphDatabase
from elasticsearch import Elasticsearch, helpers
import os, uuid

mapping_experts = {
    "mappings": {
        "properties": {
            "uuid": {"type": "keyword"},
            "name": {"type": "text"},
            "url": {"type": "keyword", "enabled": False},
            "organisations": {
                "properties": {
                    "name": {"type": "text"},
                    "url": {"type": "keyword", "enabled": False},
                }
            },
        }
    }
}
index_name_experts = 'experts'

mapping = {
    "mappings": {
        "properties": {
        "title": {"type": "text"},
        "abstract": {"type": "text"},
        "tech_abstract": {"type": "text"},
        "impact": {"type": "text"},
        "visibility": {"type": "keyword"},
        "keywords": {"type": "text"},
        "type": {"type": "keyword"},
        "document_id": {"type": "keyword"},
        "source": {
            "type": "object",
            "enabled": False
        },
        "experts": {"type": "keyword"},
        }
    }
}



'''
a simple function that gets the working path of
the Python script and returns it
'''

def get_data_from_file(file_name):
    file_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    with open(file_data) as f:
        data = json.load(f)
    return data


'''
generator to push bulk data from a JSON
file into an Elasticsearch index
'''
def bulk_json_data(json_file, _index, doc_type):
    json_list = get_data_from_file(json_file)
    for num, doc_i in enumerate(json_list):
        for doc in doc_i:
           if '_index' not in doc:
               yield {
                    "_index": _index,
                    "_id": uuid.uuid4(),
                    "_type": doc_type,
                    "_score": "1.0",
                    "_source": doc
               }
           else:
               yield {
                    "_index": doc["_index"],
                    "_id": doc["_id"],
                    "_type": doc["_type"],
                    "_score": doc["_score"],
                    "_source": doc["_source"]
               }

if __name__ == "__main__":
    index_name = 'expertise'
    with open('../common_files/constants.json') as f:
        constants = json.load(f)
    es = Elasticsearch([{'host': constants["ES_HOST_URL"], 'port': constants["ES_PORT"]}])
    # drop and create index for expertise
    print("Deleting-Creating-Loading Expertise to ES")
    es.indices.delete(index=index_name, ignore=[400, 404])
    es.indices.create(index=index_name, body=mapping, ignore=400)
   
    response = helpers.bulk(es, bulk_json_data("common_files/expertise.json", index_name, "_doc"))
    print ("\nRESPONSE:", response)
    
    print("Deleting-Creating-Loading Experts to ES")
    # drop and create index for experts
    es.indices.delete(index=index_name_experts, ignore=[400, 404])
    es.indices.create(index=index_name_experts, body=mapping_experts, ignore=400)
   
    response = helpers.bulk(es, bulk_json_data("common_files/experts.json", index_name_experts, "_doc"))
    print ("\nRESPONSE:", response)
