import configparser
import json
from tqdm import tqdm
import os

from neo4j import GraphDatabase
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

mapping_experts = {
    "mappings": {
        "properties": {
            "uuid": {"type": "keyword"},
            "name": {"type": "text"},
            "job_title": {"type": "keyword"},
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

def generate_staff_entries(driver):
    query = '''
        MATCH (person:PURE:Person)
        -[affiliation]- 
        (o:PURE:OrganisationalUnit)
        RETURN person {
            .uuid,
            .name_firstName,
            .name_lastName,
            .info_portalUrl,
            organisations: collect(o { .name_value, .info_portalUrl }),
            affiliations: collect(affiliation { .period_endDate, .jobDescription_value })
        }
    '''
    print(query)

    staff = set()
    with driver.session() as session:
        result = session.run(query)
        for r in result:
            pers_node = r['person']
            if pers_node['uuid'] in staff:
                continue
            staff.add(pers_node['uuid'])
            job_title = ''
            organisations = []
            for a, o in zip(pers_node['affiliations'], pers_node['organisations']):
                if a['period_endDate']=='':
                    organisations.append({
                        'name': o['name_value'],
                        'url': o['info_portalUrl']
                    })
                    if a['jobDescription_value'] != '':
                        job_title = a['jobDescription_value']
            body = {
                'uuid': pers_node['uuid'],
                'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
                'job_title': job_title,
                'url': pers_node['info_portalUrl'],
                'organisations': organisations,
            }
            yield {
                "_index": index_name_experts,
                "_source": body,
            }

    print(f'Found {len(staff)} staff')


if __name__ == "__main__":

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    uri = "bolt://roag.is.ed.ac.uk:7687"
    driver = GraphDatabase.driver(uri, auth=(config['auth']['USERNAME'], config['auth']['PASSWORD']))

    es = Elasticsearch()

    print(f'Creating index {index_name_experts}')
    es.indices.delete(index=index_name_experts, ignore=[400, 404])
    es.indices.create(index=index_name_experts, body=mapping_experts, ignore=400)

    bulk(es, tqdm(generate_staff_entries(driver)))