import json
import os

from tqdm import tqdm

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Search

if __name__ == "__main__":

    es = Elasticsearch()
    query = {
        "query": 
          { "bool" :
            {
              "must": [
                {"term":{"type": "OM" } },
                {"term":{"type": "profile" } }
              ] 
            } 
          } 
        } 
    
    # delete all user profiles (documents with type ["OM", "profile"]) from the index
    s = Search.from_dict(query).using(es).index('expertise')
    response = s.delete()
    print(f'Deleted {response.deleted} profile documents')

    # insert new user profiles from the json file
    # format of json must be ES bulk insert format
    profile_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profiles.json')
    with open(profile_data) as f:
        profiles = json.load(f)
    if profiles:
        bulk(es, tqdm(profiles))
    print(f'Inserted {len(profiles)} profile documents')
