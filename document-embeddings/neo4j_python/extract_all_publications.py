import json
import configparser
import os

from neo4j import GraphDatabase

def extract_publications(driver, organisation):
    query = f'''
        MATCH (o:PURE:OrganisationalUnit)            
        --(p:PURE:Person)
        --(r:PURE:ResearchOutput)
        WHERE o.name_value = '{organisation}'
        RETURN r, p
    '''
    print(query)

    research_outputs = {}
    with driver.session() as session:
        result = session.run(query)

        for r in result:
            pers_id = r['p']['uuid']
            resout_node = r['r']
            resout_id = resout_node['uuid']
            author = {
                'name': f"{r['p']['name_firstName']} {r['p']['name_lastName']}",
                'url': r['p']['info_portalUrl'],
                'uuid': pers_id,
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
                if author not in research_outputs[resout_id]['authors']:
                    research_outputs[resout_id]['authors'].append(author) 

    with open(os.path.join(os.path.join(os.path.dirname(__file__), 'outputs'), f'{organisation}-publications.json'), 'w') as f:
        json.dump(research_outputs, f, indent=2)
    print(f'Found {len(research_outputs)} research outputs')


if __name__ == "__main__":

    config = configparser.ConfigParser()
    configfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    config.read(configfile)

    uri = "bolt://roag.is.ed.ac.uk:7687"
    driver = GraphDatabase.driver(uri, auth=(config['auth']['USERNAME'], config['auth']['PASSWORD']))

    with open(os.path.join(os.path.dirname(__file__), 'uoe_organisations.json')) as f:
        organisations = json.load(f)

    for organisation in organisations:
        extract_publications(driver, organisation)


