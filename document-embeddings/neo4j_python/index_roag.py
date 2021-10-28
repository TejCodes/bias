import json
import configparser
import os

from tqdm import tqdm

from neo4j import GraphDatabase
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

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

index_name = 'expertise'

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

def generate_documents(driver):

    # Note [:AUTHOR] doesn't work because some research output use different connections
    query = '''
        MATCH (ro:PURE:ResearchOutput)
        --> (p:PURE:Person)
        RETURN ro {
            .title, 
            .uuid, 
            .abstract_value, 
            .keywords,
            .info_portalUrl,
            authors: collect(p {.uuid, .name_firstName, .name_lastName, .info_portalUrl})}
        '''
    print(query)

    nro = 0
    with driver.session() as session:
        result = session.run(query)

        for r in result:
            ro = r['ro']
            nro += 1
            names = {
                a['uuid'] : {
                    'name': f"{a['name_firstName']} {a['name_lastName']}",
                    'url': a['info_portalUrl'],
                    'uuid': a['uuid'],
                }
                for a in ro['authors']
            }

            body = {
                'title': ro['title'],
                'experts': list(names.keys()),
                'abstract': ro['abstract_value'],
                'visibility': None, # public records,
                'type': ['PURE', 'research_output'],
                'document_id': ro['uuid'],
                'keywords': ro['keywords'],
                'source': {
                    'names': list(names.values()),
                    'url': ro['info_portalUrl'],
                }
            }
            yield {
                "_index": index_name,
                "_source": body,
            }
    print(f'Found {nro} research outputs')

def generate_projects(driver):

    query = '''
        MATCH (:GTR:Organisation {name: 'University of Edinburgh'})
        -- (proj:GTR:Project)
        OPTIONAL MATCH (proj) -- (g:GTR:Person)
        <-[:ROAG_CANONICAL_ID_FOR]-()-[:ROAG_CANONICAL_ID_FOR]->
        (person:PURE:Person)
        RETURN proj {
            .title, 
            .id, 
            .href, 
            .techAbstractText,
            .abstractText, 
            .potentialImpact, 
            members: collect(person {
                .uuid, .name_firstName, .name_lastName, .info_portalUrl})}        
    '''
    print(query)

    np = 0
    with driver.session() as session:
        result = session.run(query)

        for r in result:
            proj = r['proj']
            np += 1
            # there might be duplicates
            if proj['members'] is not None:
                names = {
                    m['uuid'] : {
                        'name': f"{m['name_firstName']} {m['name_lastName']}",
                        'url': m['info_portalUrl'],
                        'uuid': m['uuid'],
                    }
                    for m in proj['members']
                }
            else:
                names = {}

            body = {
                'title': proj['title'],
                'experts': list(names.keys()),
                'abstract': proj['abstractText'],
                'tech_abstract': proj['techAbstractText'],
                'impact': proj['potentialImpact'],
                'visibility': None, # public records,
                'type': ['GTR', 'project'],
                'document_id': proj['id'],
                'source': {
                    'names': list(names.values()),
                    'url': proj['href'],
                }
            }
            yield {
                "_index": index_name,
                "_source": body,
            }
    print(f'Found {np} projects')

def generate_staff_entries(driver):
    query = '''
        MATCH (person:PURE:Person)
        -- (o:PURE:OrganisationalUnit)
        RETURN person {
            .uuid,
            .name_firstName,
            .name_lastName,
            .info_portalUrl,
            organisations: collect(o { .name_value, .info_portalUrl })}
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
            body = {
                'uuid': pers_node['uuid'],
                'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
                'organisations': [{
                    'name': org['name_value'],
                    'url': org['info_portalUrl']
                 } for org in pers_node['organisations']],
            }
            if 'info_portalUrl' in pers_node:
                body['url'] = pers_node['info_portalUrl']
            # print(json.dumps(body, indent=4))
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

    # drop and create index for research outputs and projects
    es.indices.delete(index=index_name, ignore=[400, 404])
    es.indices.create(index=index_name, body=mapping, ignore=400)

    # drop and create index for experts
    es.indices.delete(index=index_name_experts, ignore=[400, 404])
    es.indices.create(index=index_name_experts, body=mapping_experts, ignore=400)

    bulk(es, tqdm(generate_documents(driver)))
    bulk(es, tqdm(generate_projects(driver)))
    bulk(es, tqdm(generate_staff_entries(driver)))