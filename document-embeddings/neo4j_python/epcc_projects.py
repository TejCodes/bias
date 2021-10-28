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

    # epcc_staff = {}
    # uoe_staff = {}
    # research_outputs = {}
    # with driver.session() as session:
    #     result = session.run('''
    #         MATCH (o:PURE:OrganisationalUnit {name_value: "Edinburgh Parallel Computing Centre"})
    #         --(p:PURE:Person) return p
    #     ''')
    #     for r in result:
    #         pers_node = r['p']
    #         epcc_staff[pers_node['uuid']] = {
    #             'id': pers_node['uuid'],
    #             'url': pers_node['info_portalUrl'],
    #             'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
    #             'keywords': pers_node['keywords'],
    #             'organisation': 'Edinburgh Parallel Computing Centre'
    #         }
    
    projects = {}
    with driver.session() as session:
        result = session.run('''
            MATCH (o:PURE:OrganisationalUnit {name_value: "Edinburgh Parallel Computing Centre"})
            --(person:PURE:Person)
            --(project:PURE:Project) 
            return project, person
        ''')
        for r in result:
            pers_node = r['person']
            person = {
                'uuid': pers_node['uuid'],
                'url': pers_node['info_portalUrl'],
                'name': f"{pers_node['name_firstName']} {pers_node['name_lastName']}",
            }
            proj = r['project']
            if proj['uuid'] in projects:
                projects[proj['uuid']]['people'].append(person)
            else:
                projects[proj['uuid']] = {
                    'title': proj['title'],
                    'description': proj['description'],
                    'keywords': proj['keywords'],
                    'startDate': proj['period_startDate'],
                    'endDate': proj['period_endDate'],
                    'people': [person],
                }
    with open(os.path.join(os.path.dirname(__file__), 'epcc_projects.json'), 'w') as f:
        json.dump(projects, f, indent=4)
    print(f'Found {len(projects)} projects')
        