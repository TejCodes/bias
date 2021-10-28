import json
import configparser
import os

from neo4j import GraphDatabase


if __name__ == "__main__":

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    uri = "bolt://roag.is.ed.ac.uk:7687"
    driver = GraphDatabase.driver(uri, auth=(config['auth']['USERNAME'], config['auth']['PASSWORD']))

    epcc_staff = {}
    uoe_staff = {}
    research_outputs = {}
    with driver.session() as session:
        result = session.run('''
            MATCH (o:PURE:OrganisationalUnit {name_value: "Edinburgh Parallel Computing Centre"})
            --(p:PURE:Person) return p
        ''')
        for r in result:
            pers_node = r['p']
            epcc_staff[pers_node['uuid']] = {
                'id': pers_node['uuid'],
                'url': pers_node['info_portalUrl'],
                'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
                'keywords': pers_node['keywords'],
                'organisation': 'Edinburgh Parallel Computing Centre'
            }

    with driver.session() as session:
        result = session.run ('''
            MATCH (o:PURE:OrganisationalUnit {name_value: "Edinburgh Parallel Computing Centre"})            
            --(p:PURE:Person)
            --(r:PURE:ResearchOutput)
            return r, p
        ''')

        for r in result:
            pers_id = r['p']['uuid']
            if pers_id not in epcc_staff:
                uoe_staff[pers_id] = {
                    'id': pers_id,
                    'url': r['p']['info_portalUrl'],
                    'name': f"{r['p']['name_firstName']} {r['p']['name_lastName']}",
                    'keywords': r['p']['keywords'],
                }
            resout_node = r['r']
            resout_id = resout_node['uuid']
            author = {
                'name': f"{r['p']['name_firstName']} {r['p']['name_lastName']}",
                'uuid': pers_id
            }
            if not resout_id in research_outputs:
                research_outputs[resout_id] = {
                    'id': resout_id,
                    'url': resout_node['info_portalUrl'],
                    'abstract' : resout_node['abstract_value'],
                    'title': resout_node['title'],
                    'keywords': resout_node['keywords'],
                    'authors': [author]
                }
            else:
                research_outputs[resout_id]['authors'].append(author) 

    with open(os.path.join(os.path.dirname(__file__), 'epcc_publications.json'), 'w') as f:
        json.dump(research_outputs, f, indent=4)
    print(f'Found {len(research_outputs)} research outputs')